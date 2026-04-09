import uuid

from django.db import IntegrityError, models, transaction
from django.db.models import Max


class DriverProfile(models.Model):
    class EmploymentStatus(models.TextChoices):
        ONBOARDING = "onboarding", "onboarding"
        ACTIVE = "active", "active"
        LEAVE = "leave", "leave"
        RESIGNED = "resigned", "resigned"
        RETIRED = "retired", "retired"

    class QualificationStatus(models.TextChoices):
        PENDING_REVIEW = "pending_review", "pending_review"
        QUALIFIED = "qualified", "qualified"
        RESTRICTED = "restricted", "restricted"
        EXPIRED = "expired", "expired"
        REVOKED = "revoked", "revoked"

    driver_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route_no = models.PositiveIntegerField(unique=True, editable=False)
    company_id = models.UUIDField()
    fleet_id = models.UUIDField()
    name = models.CharField(max_length=255)
    external_user_name = models.CharField(max_length=120, blank=True, default="")
    ev_id = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=32)
    address = models.CharField(max_length=255)
    employment_status = models.CharField(
        max_length=32,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
    )
    qualification_status = models.CharField(
        max_length=32,
        choices=QualificationStatus.choices,
        default=QualificationStatus.QUALIFIED,
    )

    class Meta:
        ordering = ("driver_id",)

    def save(self, *args, **kwargs):
        if self.route_no is not None:
            return super().save(*args, **kwargs)

        for _ in range(5):
            self.route_no = (type(self).objects.aggregate(max_route_no=Max("route_no"))["max_route_no"] or 0) + 1
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError:
                self.route_no = None

        raise IntegrityError("Failed to allocate driver route_no.")
