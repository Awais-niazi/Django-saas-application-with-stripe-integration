from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from decimal import Decimal

from customers.models import Customer, SupportRequest
from subscriptions.models import Subscriptions, SubscriptionsPrice, UserSubscription


User = get_user_model()


class TestAuthAndCoreSmoke(TestCase):
    def setUp(self):
        self.create_product_patcher = patch("helpers.billing.create_product", return_value="prod_test_local")
        self.create_price_patcher = patch("helpers.billing.create_price", return_value="price_test_local")
        self.create_product_patcher.start()
        self.create_price_patcher.start()
        self.addCleanup(self.create_product_patcher.stop)
        self.addCleanup(self.create_price_patcher.stop)

        self.subscription = Subscriptions.objects.create(name="Growth")
        self.subscription_price = SubscriptionsPrice.objects.create(
            subscription=self.subscription,
            price=Decimal("19.00"),
        )

    def test_landing_page_loads(self):
        response = self.client.get(reverse("landing_page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beginner-friendly Django SaaS starter")

    def test_pricing_page_loads(self):
        response = self.client.get(reverse("pricing_view"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Starter")

    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("health_check_view"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})

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

    def test_logout_view_logs_user_out(self):
        user = User.objects.create_user(
            username="signedin",
            email="signedin@example.com",
            password="safe-pass-123",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("logout_view"))

        self.assertRedirects(response, reverse("landing_page"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_support_request_can_be_submitted(self):
        response = self.client.post(
            reverse("support_view"),
            {
                "name": "Awais",
                "email": "awais@example.com",
                "subject": "Need help",
                "message": "Please help me understand the billing setup.",
            },
        )

        self.assertRedirects(response, reverse("support_view"))
        self.assertTrue(SupportRequest.objects.filter(email="awais@example.com").exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard_view"))
        self.assertEqual(response.status_code, 302)

    @patch("cfehome.views.billing.stripe_is_configured", return_value=False)
    def test_checkout_view_redirects_when_stripe_not_configured(self, _mock_stripe):
        user = User.objects.create_user(
            username="checkout-user",
            email="checkout@example.com",
            password="safe-pass-123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("create_checkout_session_view", args=[self.subscription_price.id])
        )

        self.assertRedirects(response, reverse("billing_overview_view"))

    @patch("helpers.billing.create_checkout_session", return_value="https://checkout.stripe.com/test-session")
    @patch("helpers.billing.create_customer", return_value="cus_test_123")
    @patch("cfehome.views.ensure_subscription_price_stripe_ids")
    @patch("cfehome.views.billing.stripe_is_configured", return_value=True)
    def test_checkout_view_redirects_to_stripe_session(
        self,
        _mock_stripe,
        mock_ensure_subscription_price,
        _mock_create_customer,
        _mock_create_checkout,
    ):
        user = User.objects.create_user(
            username="paid-user",
            email="paid@example.com",
            password="safe-pass-123",
        )
        self.client.force_login(user)
        self.subscription_price.stripe_id = "price_test_123"
        mock_ensure_subscription_price.return_value = self.subscription_price

        response = self.client.post(
            reverse("create_checkout_session_view", args=[self.subscription_price.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://checkout.stripe.com/test-session")
        self.assertTrue(Customer.objects.filter(user=user, stripe_id="cus_test_123").exists())

    def test_billing_success_page_loads_for_authenticated_user(self):
        user = User.objects.create_user(
            username="billing-user",
            email="billing@example.com",
            password="safe-pass-123",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("billing_success_view"),
            {"session_id": "cs_test_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cs_test_123")

    def test_stripe_webhook_syncs_local_subscription(self):
        user = User.objects.create_user(
            username="webhook-user",
            email="webhook@example.com",
            password="safe-pass-123",
        )
        customer = Customer.objects.create(
            user=user,
            init_email=user.email,
            init_email_confirmed=True,
            stripe_id="cus_123",
        )

        with patch("cfehome.views.billing.construct_webhook_event") as mock_construct:
            mock_construct.return_value = {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "mode": "subscription",
                        "customer": customer.stripe_id,
                        "subscription": "sub_123",
                        "metadata": {
                            "user_id": str(user.id),
                            "subscription_price_id": str(self.subscription_price.id),
                        },
                    }
                },
            }
            response = self.client.post(
                reverse("stripe_webhook_view"),
                data="{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="sig_test",
            )

        self.assertEqual(response.status_code, 200)
        user_subscription = UserSubscription.objects.get(user=user)
        self.assertEqual(user_subscription.subscription, self.subscription)
        self.assertEqual(user_subscription.stripe_subscription_id, "sub_123")
