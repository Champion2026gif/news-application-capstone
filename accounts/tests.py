from django.contrib.auth import get_user_model
import io
from django.core.management import call_command
from django.test import TestCase

User = get_user_model()


class RoleGroupSyncTests(TestCase):
    def setUp(self):
        call_command("setup_groups", stdout=io.StringIO())

    def test_new_reader_added_to_reader_group(self):
        user = User.objects.create_user(username="r1", password="pw12345", role="READER")
        self.assertTrue(user.groups.filter(name="Reader").exists())

    def test_new_journalist_added_to_journalist_group(self):
        user = User.objects.create_user(username="j1", password="pw12345", role="JOURNALIST")
        self.assertTrue(user.groups.filter(name="Journalist").exists())

    def test_new_editor_added_to_editor_group(self):
        user = User.objects.create_user(username="e1", password="pw12345", role="EDITOR")
        self.assertTrue(user.groups.filter(name="Editor").exists())

    def test_journalist_has_empty_reader_subscription_fields(self):
        from articles.models import Publisher
        journalist = User.objects.create_user(username="j2", password="pw12345", role="JOURNALIST")
        self.assertEqual(journalist.subscriptions_publishers.count(), 0)
        self.assertEqual(journalist.subscriptions_journalists.count(), 0)

    def test_changing_role_moves_user_between_groups(self):
        user = User.objects.create_user(username="switcher", password="pw12345", role="READER")
        self.assertTrue(user.groups.filter(name="Reader").exists())
        user.role = "JOURNALIST"
        user.save()
        self.assertFalse(user.groups.filter(name="Reader").exists())
        self.assertTrue(user.groups.filter(name="Journalist").exists())

    def test_reader_can_hold_publisher_and_journalist_subscriptions(self):
        from articles.models import Publisher
        journalist = User.objects.create_user(username="j3", password="pw12345", role="JOURNALIST")
        publisher = Publisher.objects.create(name="Test Pub")
        reader = User.objects.create_user(username="r2", password="pw12345", role="READER")
        reader.subscriptions_publishers.add(publisher)
        reader.subscriptions_journalists.add(journalist)
        self.assertEqual(reader.subscriptions_publishers.count(), 1)
        self.assertEqual(reader.subscriptions_journalists.count(), 1)


class RegistrationAndDashboardTests(TestCase):
    def setUp(self):
        call_command("setup_groups", stdout=io.StringIO())
        self.registration_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }

    def register(self, username, role):
        data = {**self.registration_data, "username": username, "role": role}
        data["email"] = f"{username}@example.com"
        return self.client.post("/accounts/register/", data)

    def test_registration_page_is_public(self):
        response = self.client.get("/accounts/register/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reader")
        self.assertContains(response, "Journalist")
        self.assertContains(response, "Editor")

    def test_register_reader_logs_in_and_routes_to_reader_dashboard(self):
        response = self.register("reader_signup", "READER")
        self.assertRedirects(
            response,
            "/accounts/dashboard/",
            fetch_redirect_response=False,
        )
        user = User.objects.get(username="reader_signup")
        self.assertTrue(user.groups.filter(name="Reader").exists())
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/dashboard/reader/")
        self.assertEqual(self.client.get("/accounts/dashboard/reader/").status_code, 200)

    def test_register_journalist_logs_in_and_routes_to_journalist_dashboard(self):
        response = self.register("journalist_signup", "JOURNALIST")
        self.assertRedirects(
            response,
            "/accounts/dashboard/",
            fetch_redirect_response=False,
        )
        user = User.objects.get(username="journalist_signup")
        self.assertTrue(user.groups.filter(name="Journalist").exists())
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/dashboard/journalist/")
        self.assertEqual(self.client.get("/accounts/dashboard/journalist/").status_code, 200)

    def test_register_editor_logs_in_and_routes_to_editor_dashboard(self):
        response = self.register("editor_signup", "EDITOR")
        self.assertRedirects(
            response,
            "/accounts/dashboard/",
            fetch_redirect_response=False,
        )
        user = User.objects.get(username="editor_signup")
        self.assertTrue(user.groups.filter(name="Editor").exists())
        response = self.client.get("/accounts/dashboard/")
        self.assertRedirects(response, "/accounts/dashboard/editor/")
        self.assertEqual(self.client.get("/accounts/dashboard/editor/").status_code, 200)

    def test_reader_cannot_access_editor_dashboard(self):
        self.register("reader_locked", "READER")
        response = self.client.get("/accounts/dashboard/editor/")
        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_access_journalist_dashboard(self):
        self.register("editor_locked", "EDITOR")
        response = self.client.get("/accounts/dashboard/journalist/")
        self.assertEqual(response.status_code, 403)

    def test_login_redirects_to_role_router(self):
        User.objects.create_user(
            username="login_editor",
            password="StrongPass123!",
            role="EDITOR",
        )
        response = self.client.post(
            "/login/",
            {"username": "login_editor", "password": "StrongPass123!"},
        )
        self.assertRedirects(
            response,
            "/accounts/dashboard/",
            fetch_redirect_response=False,
        )
