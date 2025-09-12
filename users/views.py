# Core Django imports
# Logging
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from core.validators import (
    EMAIL_UNIQUE_VALIDATOR,
    USERNAME_UNIQUE_VALIDATOR,
    APIValidationMixin,
    ValidationMixin,
)

# Local imports
from .forms import (
    BusinessProfileForm,
    MinimalRegistrationForm,
    PrivateProfileForm,
    UserLoginForm,
    UserProfileForm,
    UserRegistrationForm,
    UserUpdateForm,
)
from .models import CustomUser

logger = logging.getLogger("access_logger")


class APIResponseHelper(ValidationMixin, APIValidationMixin):
    """Helper class for standardized API responses"""

    @staticmethod
    def success_response(data, status=200):
        """Return standardized success response"""
        return JsonResponse(
            {
                "status": "success",
                "data": data,
                "timestamp": timezone.now().isoformat(),
            },
            status=status,
        )

    @staticmethod
    def error_response(message, detail=None, status=400):
        """Return standardized error response"""
        response_data = {
            "status": "error",
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }
        if detail:
            response_data["detail"] = detail
        return JsonResponse(response_data, status=status)

    @staticmethod
    def validation_error_response(errors, status=400):
        """Return standardized validation error response"""
        return JsonResponse(
            {
                "status": "error",
                "message": "Validation failed",
                "validation_errors": errors,
                "timestamp": timezone.now().isoformat(),
            },
            status=400,
        )


def register(request):
    """Vista per la registrazione di nuovi utenti con form minimale"""
    if request.method == "POST":
        form = MinimalRegistrationForm(request.POST)

        if form.is_valid():
            # Additional validation using centralized validators
            try:
                # Validate email uniqueness
                EMAIL_UNIQUE_VALIDATOR(form.cleaned_data["email"])

                user = form.save()

                logger.info(
                    f"Nuovo utente registrato (minimale) - Username: {user.username} - Email: {user.email} - Onboarding: {user.onboarding_status} - Timestamp: {timezone.now()}"
                )

                # Login automatico dopo registrazione
                from django.contrib.auth import login

                login(request, user)

                messages.success(
                    request,
                    "Registrazione completata! Ora completa il tuo profilo per procedere.",
                )
                return redirect(
                    "users:profile_complete"
                )  # Redirect a completamento anagrafico

            except ValidationError as e:
                form.add_error("email", str(e))
                messages.error(request, "Email già esistente.")
        else:
            messages.error(
                request, "Ci sono errori nel form. Controlla i campi evidenziati."
            )
    else:
        form = MinimalRegistrationForm()

    context = {
        "form": form,
        "form_errors": form.errors if hasattr(form, "errors") else None,
        "is_minimal": True,  # Flag per template
    }
    return render(request, "users/register.html", context)


@login_required
def profile_complete(request):
    """Redirect al completamento profilo anagrafico nell'app cer"""
    if request.user.onboarding_status != CustomUser.OnboardingStatus.REGISTRATO:
        return redirect("core:dashboard")

    return redirect("cer:profile_completion")


def login_view(request):
    """Vista per il login degli utenti"""
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(username=email, password=password)
            if user is not None:
                # Aggiorna last_login senza validazione
                user._last_login_only = True
                user.last_login = timezone.now()
                user.save(skip_validation=True)
                login(request, user)
                return redirect("core:home")  # o qualsiasi altra pagina dopo il login
        else:
            # Non aggiungere messaggi qui, lascia che sia il form a gestire gli errori
            # Rimuovi qualsiasi chiamata a messages.error o messages.add_message
            pass
    else:
        form = UserLoginForm()

    return render(request, "users/login.html", {"form": form})


@login_required
def logout_view(request):
    if request.method == "POST":
        username = request.user.username
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT")

        logout(request)

        logger.info(
            f"Logout effettuato - Utente: {username} - "
            f"IP: {ip} - User Agent: {user_agent}"
        )

        return redirect("users:login")  # Usa il namespace completo

    return redirect("core:home")


class ProfileView(LoginRequiredMixin, View):
    """Vista per la gestione del profilo utente"""

    model = CustomUser
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get(self, request):
        # Preparazione dei form
        user_form = UserUpdateForm(instance=request.user)
        business_form = (
            BusinessProfileForm(instance=request.user)
            if request.user.legal_type == "BUSINESS"
            else None
        )

        # Context base
        context = {
            "user_form": user_form,
            "business_form": business_form,
        }

        # Statistiche utente
        context.update(
            {
                "total_logins": (
                    request.user.logins.count()
                    if hasattr(request.user, "logins")
                    else 0
                ),
                "total_documents": (
                    request.user.documents.count()
                    if hasattr(request.user, "documents")
                    else 0
                ),
                "total_plants": (
                    request.user.plants.count()
                    if hasattr(request.user, "plants")
                    else 0
                ),
            }
        )

        # Informazioni GDPR
        context.update(
            {
                "privacy_status": {
                    "accepted": getattr(request.user, "privacy_accepted", False),
                    "acceptance_date": getattr(
                        request.user, "privacy_acceptance_date", None
                    ),
                    "last_update": getattr(request.user, "last_privacy_update", None),
                }
            }
        )

        # Dati aziendali se necessario
        if request.user.is_business:
            context.update(
                {
                    "business_info": {
                        "legal_name": getattr(request.user, "legal_name", ""),
                        "vat_number": getattr(request.user, "vat_number", ""),
                        "pec": getattr(request.user, "pec", ""),
                        "sdi_code": getattr(request.user, "sdi_code", ""),
                    }
                }
            )

            # Documenti aziendali
            if hasattr(request.user, "documents"):
                context["business_documents"] = request.user.documents.all().order_by(
                    "-upload_date"
                )

        # Attività recenti
        context["recent_activity"] = {
            "last_login": request.user.last_login,
            "date_joined": request.user.date_joined,
            "profile_updates": getattr(request.user, "profile_updates", 0),
        }

        return render(request, self.template_name, context)

    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        business_form = None

        if request.user.legal_type == "BUSINESS":
            business_form = BusinessProfileForm(request.POST, instance=request.user)
            if user_form.is_valid() and business_form.is_valid():
                # Additional validation using centralized validators
                try:
                    # Validate email uniqueness (excluding current user)
                    if user_form.cleaned_data["email"] != request.user.email:
                        EMAIL_UNIQUE_VALIDATOR(user_form.cleaned_data["email"])

                    user_form.save()
                    business_form.save()
                    messages.success(
                        request, "Profilo aziendale aggiornato con successo."
                    )
                    return redirect("users:profile")
                except ValidationError as e:
                    user_form.add_error("email", str(e))
                    messages.error(request, "Email già esistente.")
        else:
            if user_form.is_valid():
                # Additional validation using centralized validators
                try:
                    # Validate email uniqueness (excluding current user)
                    if user_form.cleaned_data["email"] != request.user.email:
                        EMAIL_UNIQUE_VALIDATOR(user_form.cleaned_data["email"])

                    user_form.save()
                    messages.success(
                        request, "Profilo personale aggiornato con successo."
                    )
                    return redirect("users:profile")
                except ValidationError as e:
                    user_form.add_error("email", str(e))
                    messages.error(request, "Email già esistente.")

        context = {
            "user_form": user_form,
            "business_form": business_form,
            "privacy_status": {
                "accepted": getattr(request.user, "privacy_accepted", False),
                "acceptance_date": getattr(
                    request.user, "privacy_acceptance_date", None
                ),
                "last_update": getattr(request.user, "last_privacy_update", None),
            },
        }

        messages.error(request, "Si prega di correggere gli errori nel form.")
        return render(request, self.template_name, context)


class PrivacyPolicyView(TemplateView):
    """Vista per visualizzare la privacy policy"""

    template_name = "users/privacy_policy.html"


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Vista per il cambio password"""

    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form):
        messages.success(self.request, "Password modificata con successo.")
        return super().form_valid(form)


class DeleteAccountView(LoginRequiredMixin, View):
    """Vista per l'eliminazione dell'account"""

    template_name = "users/delete_account.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Log dell'eliminazione account per GDPR
        user_id = request.user.id
        request.user.delete()
        messages.success(request, "Account eliminato con successo.")
        # Qui potresti aggiungere la logica per conservare i dati necessari per GDPR
        return redirect("home")


class UserManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = "users/gestione_utenti.html"
    context_object_name = "users"
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get("search", "")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(fiscal_code__icontains=search)
                | Q(legal_name__icontains=search)
            )
        return queryset.order_by("-date_joined")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_sensitive"] = self.request.GET.get("show_sensitive", False)
        context["search"] = self.request.GET.get("search", "")
        context["legal_type_labels"] = dict(CustomUser.LEGAL_TYPES)
        return context


class AdminUserProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    template_name = "users/admin_profile.html"
    form_class = UserProfileForm

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse_lazy("users:management")

    def form_valid(self, form):
        messages.success(self.request, "Profilo utente aggiornato con successo")
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = CustomUser
    template_name = "users/user_detail.html"
    context_object_name = "profile_user"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plants"] = self.object.plants.all()
        return context
