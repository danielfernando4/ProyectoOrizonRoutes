from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from .models import User


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse("users:register")

    def test_get_register_shows_form(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_post_register_creates_user_with_role_conductor(self):
        data = {
            "username": "conductor1",
            "email": "conductor1@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "role": "conductor",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, "conductor1")
        self.assertEqual(user.email, "conductor1@example.com")
        self.assertEqual(user.role, "conductor")
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_post_register_creates_user_with_role_pasajero(self):
        data = {
            "username": "pasajero1",
            "email": "pasajero1@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "role": "pasajero",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.role, "pasajero")
        self.assertRedirects(response, reverse("trips:search"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_duplicate_email_shows_error(self):
        User.objects.create_user(
            username="existing",
            email="dup@example.com",
            password="testpass123",
        )
        data = {
            "username": "newuser",
            "email": "dup@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "role": "pasajero",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_username_shows_error(self):
        User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="testpass123",
        )
        data = {
            "username": "existing",
            "email": "new@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "role": "pasajero",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="new@example.com").count(), 0)

    def test_password_mismatch_shows_error(self):
        data = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "testpass123",
            "password2": "differentpass",
            "role": "pasajero",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse("users:login")
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
            role="pasajero",
        )

    def test_get_login_shows_form(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_post_login_valid_credentials(self):
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(self.login_url, data)
        self.assertRedirects(response, reverse("trips:search"))

    def test_post_login_invalid_credentials(self):
        data = {"username": "testuser", "password": "wrongpass"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_post_login_invalid_username(self):
        data = {"username": "nouser", "password": "testpass123"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_authenticated_user_redirected_from_login(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse("trips:search"))


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse("users:logout")
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
            role="pasajero",
        )

    def test_post_logout_terminates_session(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, reverse("users:login"))
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 302)

    def test_logout_requires_login(self):
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse("users:profile")
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
            role="pasajero",
        )

    def test_profile_requires_login(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)

    def test_profile_shows_user_data(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")
        self.assertContains(response, "testuser")
        self.assertContains(response, "Pasajero")


class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.conductor = User.objects.create_user(
            username="cond", email="cond@example.com",
            password="testpass123", role="conductor",
        )
        self.pasajero = User.objects.create_user(
            username="pasaj", email="pasaj@example.com",
            password="testpass123", role="pasajero",
        )

    def test_conductor_has_conductor_role(self):
        self.assertEqual(self.conductor.role, "conductor")

    def test_pasajero_has_pasajero_role(self):
        self.assertEqual(self.pasajero.role, "pasajero")

    def test_profile_does_not_expose_role_change(self):
        self.client.login(username="cond", password="testpass123")
        response = self.client.get(reverse("users:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conductor")
        self.assertNotContains(response, "Cambiar rol")


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123",
            role="pasajero",
        )
        self.reset_url = reverse("users:password_reset")
        self.done_url = reverse("users:password_reset_done")
        self.complete_url = reverse("users:password_reset_complete")

    def test_password_reset_valid_email(self):
        response = self.client.post(self.reset_url, {"email": "testuser@example.com"}, follow=True)
        self.assertContains(response, "reset-url")

    def test_password_reset_invalid_email(self):
        response = self.client.post(self.reset_url, {"email": "noexiste@example.com"}, follow=True)
        self.assertNotContains(response, "reset-url")

    def test_password_reset_confirm_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        validate_url = reverse("users:password_reset_confirm", kwargs={"uidb64": uid, "token": token})

        response = self.client.get(validate_url)
        self.assertEqual(response.status_code, 302)
        set_password_url = response.url
        response = self.client.get(set_password_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/password_reset_confirm.html")
        self.assertContains(response, "Establecer Nueva Contraseña")

        response = self.client.post(set_password_url, {
            "new_password1": "newtestpass456",
            "new_password2": "newtestpass456",
        })
        self.assertRedirects(response, self.complete_url)

        login_success = self.client.login(username="testuser", password="newtestpass456")
        self.assertTrue(login_success)

    def test_password_reset_confirm_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_url = reverse("users:password_reset_confirm", kwargs={"uidb64": uid, "token": "bad-token"})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "inválido")
