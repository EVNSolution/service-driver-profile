import uuid

from django.http import Http404
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
from drivers.permissions import AuthenticatedReadWrite
from drivers.serializers import CheckEvIdResultSerializer, DriverProfileSerializer, HealthSerializer


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
        company_id = request.query_params.get("company_id")
        ev_id = request.query_params.get("ev_id")
        if not company_id or not ev_id:
            return Response(
                {"code": "invalid_request", "message": "company_id and ev_id are required.", "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_duplicate = DriverProfile.objects.filter(company_id=company_id, ev_id=ev_id).exists()
        return Response({"is_duplicate": is_duplicate})
