from django.urls import path

from drivers.views import CheckEvIdView, DriverDetailView, DriverListCreateView, EnsureExternalUsersView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("", DriverListCreateView.as_view(), name="driver-list"),
    path("check-ev-id/", CheckEvIdView.as_view(), name="driver-check-ev-id"),
    path("ensure-external-users/", EnsureExternalUsersView.as_view(), name="driver-ensure-external-users"),
    path("<str:driver_ref>/", DriverDetailView.as_view(), name="driver-detail"),
]
