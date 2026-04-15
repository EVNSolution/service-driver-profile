Source: https://lessons.md

# service-driver-profile Lessons.md

This repo owns driver profile truth only. Account/auth, organization, and assignment data can be read together in UI flows, but their write truth stays in their own runtimes.

The honest external proof is a protected read path such as `/api/drivers/`, not only `/health/`. A real protected read exercises gateway routing, JWT handling, queryset wiring, and serializer output together.
