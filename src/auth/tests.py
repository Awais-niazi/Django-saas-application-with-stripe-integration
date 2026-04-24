from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


class AuthViewsTests(TestCase):
    def test_login_view_requires_credentials(self):
        response = self.client.post(
            reverse("login_view"),
            {"username": "", "password": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username and password are required.")

    def test_login_view_logs_user_in_with_valid_credentials(self):
        user = User.objects.create_user(
            username="awais",
            email="awais@example.com",
            password="safe-pass-123",
        )

        response = self.client.post(
            reverse("login_view"),
            {"username": "awais", "password": "safe-pass-123"},
        )

        self.assertRedirects(response, reverse("home_view"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_register_view_requires_all_fields(self):
        response = self.client.post(
            reverse("register_view"),
            {"username": "", "email": "", "password": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username, email, and password are required.")

    def test_register_view_rejects_duplicate_username(self):
        User.objects.create_user(
            username="awais",
            email="first@example.com",
            password="safe-pass-123",
        )

        response = self.client.post(
            reverse("register_view"),
            {
                "username": "Awais",
                "email": "second@example.com",
                "password": "safe-pass-123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "That username is already taken.")

    def test_register_view_creates_user_and_logs_them_in(self):
        response = self.client.post(
            reverse("register_view"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "safe-pass-123",
            },
        )

        self.assertRedirects(response, reverse("home_view"))
        self.assertTrue(
            User.objects.filter(username="newuser", email="newuser@example.com").exists()
        )
