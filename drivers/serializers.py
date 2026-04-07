from rest_framework import serializers

from drivers.models import DriverProfile


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()


class CheckEvIdResultSerializer(serializers.Serializer):
    is_duplicate = serializers.BooleanField()


class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = (
            "driver_id",
            "route_no",
            "company_id",
            "fleet_id",
            "name",
            "ev_id",
            "phone_number",
            "address",
            "employment_status",
            "qualification_status",
        )
        extra_kwargs = {
            "employment_status": {"required": False},
            "qualification_status": {"required": False},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        company_id = attrs.get("company_id", getattr(self.instance, "company_id", None))
        ev_id = attrs.get("ev_id", getattr(self.instance, "ev_id", None))
        queryset = DriverProfile.objects.filter(company_id=company_id, ev_id=ev_id)
        if self.instance is not None:
            queryset = queryset.exclude(driver_id=self.instance.driver_id)
        if company_id is not None and ev_id and queryset.exists():
            raise serializers.ValidationError({"ev_id": ["EV ID already exists for this company."]})
        return attrs
