from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings

SQLITE_DB_SETTINGS = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


@override_settings(
    DATABASES=SQLITE_DB_SETTINGS,
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage",
)
class CSRFCookieTests(TestCase):
    def test_csrf_cookie_sent_when_ssl_disabled(self):
        """A CSRF cookie is issued on the login page when SSL is disabled."""
        self.assertFalse(settings.CSRF_COOKIE_SECURE)
        client = Client()
        response = client.get(reverse("users:login"))
        self.assertIn("csrftoken", response.cookies)

    @override_settings(USE_SSL=True, CSRF_COOKIE_SECURE=True, SESSION_COOKIE_SECURE=True)
    def test_csrf_cookie_marked_secure_when_ssl_enabled(self):
        """The CSRF cookie is marked secure when SSL is enabled."""
        client = Client()
        response = client.get(reverse("users:login"), secure=True)
        csrf_cookie = response.cookies.get("csrftoken")
        self.assertIsNotNone(csrf_cookie)
        self.assertTrue(csrf_cookie["secure"])
