# cer/urls.py
from django.urls import path

from . import views

app_name = "cer"

urlpatterns = [
    # Completamento profilo anagrafico
    path("profile-completion/", views.profile_completion, name="profile_completion"),
    # Wizard onboarding
    path("onboarding/", views.onboarding_wizard, name="onboarding_wizard"),
    path("onboarding/step/<int:step>/", views.onboarding_step, name="onboarding_step"),
    path("onboarding/status/", views.onboarding_status, name="onboarding_status"),
    path("resolve-pod/", views.resolve_pod, name="resolve_pod"),
]
