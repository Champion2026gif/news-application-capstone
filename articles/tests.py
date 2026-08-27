from django.contrib.auth import get_user_model
import io
from unittest.mock import patch

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from .models import Article, Publisher

User = get_user_model()


class ArticleApprovalViewTests(TestCase):
    """Access-control tests for the template-based editorial queue/approval views."""

    def setUp(self):
        call_command("setup_groups", stdout=io.StringIO())
        self.editor = User.objects.create_user(username="v_editor", password="pw12345", role="EDITOR")
        self.journalist = User.objects.create_user(username="v_journo", password="pw12345", role="JOURNALIST")
        self.reader = User.objects.create_user(username="v_reader", password="pw12345", role="READER")
        self.publisher = Publisher.objects.create(name="View Pub")
        self.publisher.journalists.add(self.journalist)
        self.article = Article.objects.create(
            title="Pending Piece", content="content", author=self.journalist, publisher=self.publisher,
        )

    def test_anonymous_user_redirected_from_pending_queue(self):
        response = self.client.get(reverse("articles:pending_list"))
        self.assertEqual(response.status_code, 302)

    def test_reader_forbidden_from_pending_queue(self):
        self.client.login(username="v_reader", password="pw12345")
        response = self.client.get(reverse("articles:pending_list"))
        self.assertEqual(response.status_code, 403)

    def test_editor_can_view_pending_queue(self):
        self.client.login(username="v_editor", password="pw12345")
        response = self.client.get(reverse("articles:pending_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending Piece")

    @patch("articles.signals.requests.post")
    def test_editor_can_approve_article(self, mock_post):
        self.client.login(username="v_editor", password="pw12345")
        response = self.client.post(reverse("articles:approve_article", args=[self.article.pk]))
        self.assertEqual(response.status_code, 302)
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)
        self.assertEqual(self.article.approved_by, self.editor)

    def test_journalist_cannot_approve_article(self):
        self.client.login(username="v_journo", password="pw12345")
        response = self.client.post(reverse("articles:approve_article", args=[self.article.pk]))
        self.article.refresh_from_db()
        self.assertFalse(self.article.approved)  # rejected by view-level check

    def test_journalist_can_submit_article_via_form(self):
        self.client.login(username="v_journo", password="pw12345")
        response = self.client.post(reverse("articles:article_create"), {
            "title": "Fresh Submission", "content": "New content here.", "publisher": self.publisher.id,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Article.objects.filter(title="Fresh Submission", approved=False).exists())

    def test_reader_cannot_submit_article_via_form(self):
        self.client.login(username="v_reader", password="pw12345")
        response = self.client.post(reverse("articles:article_create"), {
            "title": "Should Not Exist", "content": "x",
        })
        self.assertFalse(Article.objects.filter(title="Should Not Exist").exists())
