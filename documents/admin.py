# documents/admin.py
from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["type", "source", "plant", "uploaded_by", "uploaded_at"]
    list_filter = ["type", "source", "uploaded_at"]
    search_fields = ["notes", "uploaded_by__username", "plant__name"]
    date_hierarchy = "uploaded_at"
    readonly_fields = ["source"]
