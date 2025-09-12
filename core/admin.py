"""
Admin configuration for CerCollettiva - Django Admin Standard
"""

from datetime import datetime, time, timedelta

from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from core.main_models import (
    Alert,
    CERConfiguration,
    CERDistributionConfiguration,
    CERMembership,
    GSEIncomeTracking,
    MemberRegistry,
    MembershipCard,
    Plant,
    PlantDocument,
    PlantMeasurement,
)
from documents.models import Document

# Import models from other apps
from energy.models import DeviceConfiguration, DeviceMeasurement, MQTTBroker
from users.models import CustomUser

from .views import CerDashboardView

# Register your models here.


class CERAdminSite(admin.AdminSite):
    site_header = "CerCollettiva Admin"
    site_title = "CerCollettiva"
    index_title = "Amministrazione CerCollettiva"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Dashboard URLs
            path(
                "dashboard/",
                self.admin_view(CerDashboardView.as_view()),
                name="admin_dashboard",
            ),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        """
        Display the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        app_list = self.get_app_list(request)

        context = {
            **self.each_context(request),
            "title": self.index_title,
            "app_list": app_list,
            **(extra_context or {}),
        }

        request.current_app = self.name

        return TemplateResponse(
            request,
            self.index_template or "admin/index.html",
            context,
        )


# Create custom admin site instance
ceradmin = CERAdminSite(name="ceradmin")
admin_site = ceradmin


# Register models with custom admin site
@admin.register(CERConfiguration, site=ceradmin)
class CERConfigurationAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "primary_substation", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "code", "primary_substation"]
    ordering = ["-created_at"]


@admin.register(CERMembership, site=ceradmin)
class CERMembershipAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "cer_configuration",
        "role",
        "is_active",
        "document_verified",
        "joined_at",
    ]
    list_filter = ["role", "is_active", "document_verified", "joined_at"]
    search_fields = ["user__username", "user__email", "cer_configuration__name"]
    ordering = ["-joined_at"]


@admin.register(Plant, site=ceradmin)
class PlantAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "pod_code",
        "plant_type",
        "owner",
        "is_active",
        "created_at",
    ]
    list_filter = ["plant_type", "is_active", "created_at"]
    search_fields = ["name", "pod_code", "owner__username", "owner__email"]
    ordering = ["-created_at"]


@admin.register(PlantMeasurement, site=ceradmin)
class PlantMeasurementAdmin(admin.ModelAdmin):
    list_display = ["plant", "variable_type", "value", "quality", "timestamp"]
    list_filter = ["variable_type", "quality", "timestamp"]
    search_fields = ["plant__name", "plant__pod_code"]
    ordering = ["-timestamp"]


@admin.register(PlantDocument, site=ceradmin)
class PlantDocumentAdmin(admin.ModelAdmin):
    list_display = ["plant", "name", "document_type", "uploaded_at"]
    list_filter = ["document_type", "uploaded_at"]
    search_fields = ["plant__name", "name"]
    ordering = ["-uploaded_at"]


@admin.register(Alert, site=ceradmin)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["title", "type", "is_read", "created_at"]
    list_filter = ["type", "is_read", "created_at"]
    search_fields = ["title", "message"]
    ordering = ["-created_at"]


@admin.register(MembershipCard, site=ceradmin)
class MembershipCardAdmin(admin.ModelAdmin):
    list_display = [
        "card_number",
        "membership",
        "is_active",
        "membership_fee_paid",
        "issue_date",
        "expiry_date",
    ]
    list_filter = ["is_active", "membership_fee_paid", "issue_date", "expiry_date"]
    search_fields = [
        "card_number",
        "membership__user__username",
        "membership__cer_configuration__name",
    ]
    ordering = ["-issue_date"]


@admin.register(MemberRegistry, site=ceradmin)
class MemberRegistryAdmin(admin.ModelAdmin):
    list_display = ["membership", "cer_configuration", "registration_date"]
    list_filter = ["cer_configuration", "registration_date"]
    search_fields = [
        "membership__user__username",
        "membership__user__fiscal_code",
        "cer_configuration__name",
    ]
    ordering = ["-registration_date"]


@admin.register(CERDistributionConfiguration, site=ceradmin)
class CERDistributionConfigurationAdmin(admin.ModelAdmin):
    list_display = ["cer_configuration", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active", "created_at", "updated_at"]
    search_fields = ["cer_configuration__name", "cer_configuration__code"]
    ordering = ["-created_at"]


@admin.register(GSEIncomeTracking, site=ceradmin)
class GSEIncomeTrackingAdmin(admin.ModelAdmin):
    list_display = ["cer_configuration", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["cer_configuration__name", "cer_configuration__code"]
    ordering = ["-created_at"]


# Energy models
@admin.register(DeviceConfiguration, site=ceradmin)
class DeviceConfigurationAdmin(admin.ModelAdmin):
    list_display = ["name", "device_type", "vendor", "is_active", "created_at"]
    list_filter = ["device_type", "is_active", "created_at"]
    search_fields = ["name", "device_id", "vendor", "model"]
    ordering = ["-created_at"]


@admin.register(DeviceMeasurement, site=ceradmin)
class DeviceMeasurementAdmin(admin.ModelAdmin):
    list_display = ["device", "plant", "quality", "timestamp"]
    list_filter = ["quality", "timestamp"]
    search_fields = ["device__device_id", "plant__name"]
    ordering = ["-timestamp"]


@admin.register(MQTTBroker, site=ceradmin)
class MQTTBrokerAdmin(admin.ModelAdmin):
    list_display = ["name", "host", "port", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "host"]
    ordering = ["-created_at"]


# Documents models
@admin.register(Document, site=ceradmin)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["uploaded_at", "uploaded_by"]
    list_filter = ["uploaded_at"]
    search_fields = ["content"]
    ordering = ["-uploaded_at"]


# Users models
@admin.register(CustomUser, site=ceradmin)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "fiscal_code",
        "legal_type",
        "profit_type",
        "is_active",
        "is_staff",
        "date_joined",
    ]
    list_filter = ["legal_type", "profit_type", "is_active", "is_staff", "date_joined"]
    search_fields = [
        "username",
        "email",
        "first_name",
        "last_name",
        "fiscal_code",
        "vat_number",
    ]
    ordering = ["-date_joined"]
