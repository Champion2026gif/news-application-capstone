"""
Tests for the Option-1 (Django signals) approval side effects:
  - emailing subscribers
  - POSTing to the internal /api/approved/ endpoint via `requests`

Both external calls are mocked so the test suite runs offline and fast.
"""
from unittest.mock import patch

from django.core import mail
from django.test import TestCase

from .factories import create_article, create_publisher, create_user, ensure_groups


class ApprovalSignalTests(TestCase):
    def setUp(self):
        ensure_groups()
        self.editor = create_user("sigeditor", "EDITOR")
        self.journalist = create_user("sigjourno", "JOURNALIST")
        self.publisher = create_publisher(journalists=[self.journalist])

        self.reader_pub_sub = create_user("pubsub_reader", "READER")
        self.reader_pub_sub.subscriptions_publishers.add(self.publisher)

        self.reader_journo_sub = create_user("journosub_reader", "READER")
        self.reader_journo_sub.subscriptions_journalists.add(self.journalist)

        self.uninterested_reader = create_user("uninterested", "READER")

    @patch("articles.signals.requests.post")
    def test_approving_article_emails_subscribed_readers(self, mock_post):
        article = create_article(self.journalist, self.publisher, approved=False, title="Breaking News")
        article.approve(editor=self.editor)

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn(self.reader_pub_sub.email, sent.to)
        self.assertIn(self.reader_journo_sub.email, sent.to)
        self.assertNotIn(self.uninterested_reader.email, sent.to)
        self.assertIn("Breaking News", sent.subject)

    @patch("articles.signals.requests.post")
    def test_approving_article_posts_to_internal_api(self, mock_post):
        article = create_article(self.journalist, self.publisher, approved=False, title="Wire Story")
        article.approve(editor=self.editor)

        self.assertTrue(mock_post.called)
        called_url = mock_post.call_args.args[0]
        called_json = mock_post.call_args.kwargs["json"]
        self.assertTrue(called_url.endswith("/api/approved/"))
        self.assertEqual(called_json["title"], "Wire Story")
        self.assertEqual(called_json["author"], self.journalist.username)

    @patch("articles.signals.requests.post")
    def test_saving_already_approved_article_again_does_not_resend_notifications(self, mock_post):
        article = create_article(self.journalist, self.publisher, approved=False, title="Old News")
        article.approve(editor=self.editor)
        self.assertEqual(len(mail.outbox), 1)

        # Simulate a later, unrelated save (e.g. editing content) within the
        # same Python object - the transient flag prevents duplicate sends.
        article.content = "Edited content."
        article.save()

        self.assertEqual(len(mail.outbox), 1)  # still just one email

    @patch("articles.signals.requests.post")
    def test_creating_unapproved_article_sends_no_notifications(self, mock_post):
        create_article(self.journalist, self.publisher, approved=False, title="Draft Only")
        self.assertEqual(len(mail.outbox), 0)
        mock_post.assert_not_called()

    def test_requests_exception_does_not_break_approval(self):
        """If the internal API is unreachable, approval must still succeed."""
        import requests as requests_module
        with patch("articles.signals.requests.post", side_effect=requests_module.exceptions.ConnectionError):
            article = create_article(self.journalist, self.publisher, approved=False, title="Resilient Story")
            article.approve(editor=self.editor)
        article.refresh_from_db()
        self.assertTrue(article.approved)


class ApprovedArticleAPIViewTests(TestCase):
    """Direct tests of the /api/approved/ endpoint the signal calls."""

    def setUp(self):
        ensure_groups()

    def test_post_valid_payload_creates_log_entry(self):
        from api.models import ApprovedArticleLog
        response = self.client.post(
            "/api/approved/",
            data={"article_id": 1, "title": "Logged Story", "author": "someone", "publisher": "Daily"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ApprovedArticleLog.objects.count(), 1)

    def test_post_missing_fields_returns_400(self):
        response = self.client.post("/api/approved/", data={"title": "Incomplete"}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
