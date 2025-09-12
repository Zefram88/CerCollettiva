# cer/tests.py
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from core.main_models import CERConfiguration, CERMembership, Plant
from users.models import CustomUser

from .models import MemberProfile

User = get_user_model()


class MemberProfileModelTest(TestCase):
    """Test per il modello MemberProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Mario",
            last_name="Rossi",
        )

    def test_member_profile_creation(self):
        """Test creazione automatica MemberProfile tramite signal"""
        # Il signal dovrebbe creare automaticamente il MemberProfile
        self.assertTrue(hasattr(self.user, "member_profile"))
        self.assertEqual(self.user.member_profile.user, self.user)

    def test_member_profile_str(self):
        """Test rappresentazione stringa MemberProfile"""
        expected = f"{self.user.get_full_name()} - Profilo CER"
        self.assertEqual(str(self.user.member_profile), expected)

    def test_onboarding_data_default(self):
        """Test che onboarding_data sia inizializzato come dict vuoto"""
        profile = self.user.member_profile
        self.assertEqual(profile.onboarding_data, {})
        self.assertIsInstance(profile.onboarding_data, dict)

    def test_onboarding_data_storage(self):
        """Test salvataggio dati onboarding nel JSONField"""
        profile = self.user.member_profile
        test_data = {
            "step_1": {"member_type": "PRIVATE", "profit_type": "NON_PROFIT"},
            "step_2": {"pod_code": "IT001E12345678", "cer_configuration": 1},
        }

        # Aggiungi codice fiscale per evitare errori di validazione
        profile.fiscal_code = "RSSMRA80A01H501U"
        profile.onboarding_data = test_data
        profile.save()

        # Ricarica dal database
        profile.refresh_from_db()
        self.assertEqual(profile.onboarding_data, test_data)
        self.assertEqual(profile.onboarding_data["step_1"]["member_type"], "PRIVATE")


class OnboardingViewsTest(TestCase):
    """Test per le view del wizard onboarding"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Mario",
            last_name="Rossi",
        )
        self.cer = CERConfiguration.objects.create(
            name="CER Test", code="CER001", description="CER di test", is_active=True
        )

    def test_onboarding_wizard_redirect_not_logged_in(self):
        """Test redirect se utente non autenticato"""
        response = self.client.get(reverse("cer:onboarding_wizard"))
        self.assertRedirects(
            response, f'/users/login/?next={reverse("cer:onboarding_wizard")}'
        )

    def test_onboarding_wizard_logged_in(self):
        """Test accesso wizard per utente autenticato"""
        # Imposta lo stato corretto per l'utente
        self.user.onboarding_status = CustomUser.OnboardingStatus.ANAGRAFICA_COMPLETA
        self.user.save()

        # Aggiungi codice fiscale al profilo per renderlo completo
        profile = self.user.member_profile
        profile.fiscal_code = "RSSMRA80A01H501U"
        profile.phone = "1234567890"
        profile.address = "Via Roma 1"
        profile.city = "Roma"
        profile.zip_code = "00100"
        profile.province = "RM"
        profile.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("cer:onboarding_wizard"))
        self.assertEqual(response.status_code, 302)  # Redirect al primo step

    def test_onboarding_step_1_post(self):
        """Test invio dati step 1"""
        # Imposta lo stato corretto per l'utente
        self.user.onboarding_status = CustomUser.OnboardingStatus.ANAGRAFICA_COMPLETA
        self.user.save()

        # Aggiungi codice fiscale al profilo per renderlo completo
        profile = self.user.member_profile
        profile.fiscal_code = "RSSMRA80A01H501U"
        profile.phone = "1234567890"
        profile.address = "Via Roma 1"
        profile.city = "Roma"
        profile.zip_code = "00100"
        profile.province = "RM"
        profile.save()

        self.client.login(username="testuser", password="testpass123")

        data = {
            "member_type": "PRIVATE",
            "profit_type": "NON_PROFIT",
            "legal_representative_name": "Mario Rossi",
            "legal_representative_surname": "Rossi",
            "legal_representative_fiscal_code": "RSSMRA80A01H501U",
            "legal_representative_birth_date": "1980-01-01",
            "legal_representative_birth_place": "Roma",
            "legal_representative_birth_province": "RM",
            "legal_representative_birth_country": "IT",
            "legal_representative_residence_address": "Via Roma 1",
            "legal_representative_residence_city": "Roma",
            "legal_representative_residence_province": "RM",
            "legal_representative_residence_cap": "00100",
            "legal_representative_residence_country": "IT",
            "legal_representative_domicile_address": "Via Roma 1",
            "legal_representative_domicile_city": "Roma",
            "legal_representative_domicile_province": "RM",
            "legal_representative_domicile_cap": "00100",
            "legal_representative_domicile_country": "IT",
            "next": "1",  # Pulsante per andare al prossimo step
        }

        response = self.client.post(reverse("cer:onboarding_step", args=[1]), data)
        self.assertEqual(response.status_code, 302)  # Redirect al prossimo step

        # Verifica che i dati siano stati salvati
        profile = self.user.member_profile
        profile.refresh_from_db()  # Ricarica dal database
        self.assertIn("step_1", profile.onboarding_data)
        self.assertEqual(profile.onboarding_data["step_1"]["member_type"], "PRIVATE")
