import uuid

from django.core.paginator import EmptyPage, Paginator
from django.http import Http404
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from drf_spectacular.types import OpenApiTypes
    from drf_spectacular.utils import OpenApiParameter, extend_schema
except ModuleNotFoundError:
    class OpenApiTypes:
        UUID = "string"
        STR = "string"

    class OpenApiParameter:
        QUERY = "query"

        def __init__(self, *args, **kwargs):
            pass

    def extend_schema(*args, **kwargs):
        def decorator(target):
            return target

        return decorator

from drivers.models import DriverProfile
from drivers.name_utils import derive_driver_name_from_external_user_name
from drivers.permissions_navigation import require_nav_access
from drivers.permissions import AuthenticatedReadWrite
from drivers.serializers import (
    CheckEvIdResultSerializer,
    DriverProfileSerializer,
    EnsureExternalUsersRequestSerializer,
    EnsureExternalUsersResponseSerializer,
    HealthSerializer,
)

class HealthView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: HealthSerializer})
    def get(self, request):
        return Response({"status": "ok"})


class DriverListCreateView(generics.ListCreateAPIView):
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer
    permission_classes = [AuthenticatedReadWrite]

    def get_queryset(self):
        queryset = super().get_queryset()
        external_user_name = self.request.query_params.get("external_user_name")
        company_id = self.request.query_params.get("company_id")
        fleet_id = self.request.query_params.get("fleet_id")
        if external_user_name:
            queryset = queryset.filter(external_user_name=external_user_name)
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if fleet_id:
            queryset = queryset.filter(fleet_id=fleet_id)
        return queryset.order_by("route_no", "driver_id")

    def get(self, request, *args, **kwargs):
        require_nav_access(request, "drivers")
        return super().get(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")

        if page is None and page_size is None:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        try:
            page_number = int(page or "1")
            page_limit = int(page_size or "10")
            if page_number < 1 or page_limit < 1:
                raise ValueError
        except ValueError:
            return Response(
                {
                    "code": "invalid_request",
                    "message": "page and page_size must be positive integers.",
                    "details": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        paginator = Paginator(queryset, page_limit)
        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages or 1)

        serializer = self.get_serializer(page_obj.object_list, many=True)
        return Response(
            {
                "count": paginator.count,
                "page": page_obj.number,
                "page_size": page_limit,
                "results": serializer.data,
            }
        )


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer
    lookup_field = "driver_id"
    lookup_url_kwarg = "driver_ref"
    permission_classes = [AuthenticatedReadWrite]

    def get_object(self):
        lookup_value = self.kwargs[self.lookup_url_kwarg]
        queryset = self.filter_queryset(self.get_queryset())
        q_parts: list[Q] = []
        if lookup_value.isdigit():
            q_parts.append(Q(route_no=int(lookup_value)))
        try:
            q_parts.append(Q(driver_id=uuid.UUID(lookup_value)))
        except ValueError:
            pass

        if not q_parts:
            raise Http404

        filters = q_parts[0]
        for part in q_parts[1:]:
            filters |= part
        obj = get_object_or_404(queryset, filters)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        require_nav_access(request, "drivers")
        return super().get(request, *args, **kwargs)


class CheckEvIdView(APIView):
    permission_classes = [AuthenticatedReadWrite]

    @extend_schema(
        parameters=[
            OpenApiParameter("company_id", OpenApiTypes.UUID, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("ev_id", OpenApiTypes.STR, OpenApiParameter.QUERY, required=True),
        ],
        responses={200: CheckEvIdResultSerializer},
    )
    def get(self, request):
        require_nav_access(request, "drivers")
        company_id = request.query_params.get("company_id")
        ev_id = request.query_params.get("ev_id")
        if not company_id or not ev_id:
            return Response(
                {"code": "invalid_request", "message": "company_id and ev_id are required.", "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_duplicate = DriverProfile.objects.filter(company_id=company_id, ev_id=ev_id).exists()
        return Response({"is_duplicate": is_duplicate})


class EnsureExternalUsersView(APIView):
    permission_classes = [AuthenticatedReadWrite]

    @extend_schema(
        request=EnsureExternalUsersRequestSerializer,
        responses={200: EnsureExternalUsersResponseSerializer},
    )
    def post(self, request):
        serializer = EnsureExternalUsersRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "code": "invalid_request",
                    "message": "Driver auto-create requires company_id, fleet_id, and at least one external_user_name.",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        company_id = serializer.validated_data["company_id"]
        fleet_id = serializer.validated_data["fleet_id"]
        external_user_names = serializer.validated_data["external_user_names"]

        existing_drivers = DriverProfile.objects.filter(
            company_id=company_id,
            fleet_id=fleet_id,
            external_user_name__in=external_user_names,
        ).order_by("route_no", "driver_id")
        driver_by_external_name: dict[str, DriverProfile] = {}
        for driver in existing_drivers:
            driver_by_external_name.setdefault(driver.external_user_name, driver)

        created_external_user_names: list[str] = []
        existing_external_user_names: list[str] = []
        with transaction.atomic():
            for external_user_name in external_user_names:
                existing_driver = driver_by_external_name.get(external_user_name)
                if existing_driver is not None:
                    existing_external_user_names.append(external_user_name)
                    continue

                created_driver = DriverProfile.objects.create(
                    company_id=company_id,
                    fleet_id=fleet_id,
                    name=derive_driver_name_from_external_user_name(external_user_name),
                    external_user_name=external_user_name,
                    ev_id="",
                    phone_number="",
                    address="",
                )
                driver_by_external_name[external_user_name] = created_driver
                created_external_user_names.append(external_user_name)

        ordered_drivers = [driver_by_external_name[external_user_name] for external_user_name in external_user_names]
        return Response(
            {
                "drivers": DriverProfileSerializer(ordered_drivers, many=True).data,
                "created_external_user_names": created_external_user_names,
                "existing_external_user_names": existing_external_user_names,
            }
        )
