# documents/urls.py
from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("upload/<int:plant_id>/", views.DocumentUploadView.as_view(), name="upload"),
    path("list/", views.DocumentListView.as_view(), name="list"),
    path("<int:pk>/", views.DocumentDetailView.as_view(), name="detail"),
    path("delete/<int:pk>/", views.DocumentDeleteView.as_view(), name="delete"),
    # Aggungiamo le URLs per Gaudì
    path(
        "plant/<int:plant_id>/gaudi/upload/",
        views.upload_gaudi_attestation,
        name="upload_gaudi",
    ),
    path("gaudi/<int:pk>/status/", views.gaudi_processing_status, name="gaudi_status"),
    path(
        "gaudi/<int:pk>/details/", views.gaudi_attestation_details, name="gaudi_details"
    ),
]
