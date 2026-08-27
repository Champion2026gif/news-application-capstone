"""
Core API tests: role-based access, reader subscriptions, journalist
create, editor approve/delete. Uses force_authenticate to isolate API
logic from the JWT mechanism (which is covered separately in
test_auth.py).
"""
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from articles.models import Article

from .factories import create_article, create_publisher, create_user, ensure_groups


class ArticleListTests(APITestCase):
    def setUp(self):
        ensure_groups()
        self.editor = create_user("editor1", "EDITOR")
        self.journalist = create_user("journo1", "JOURNALIST")
        self.other_journalist = create_user("journo2", "JOURNALIST")
        self.reader = create_user("reader1", "READER")
        self.publisher = create_publisher(journalists=[self.journalist])

        self.approved = create_article(self.journalist, self.publisher, approved=True, title="Approved One")
        self.pending = create_article(self.journalist, self.publisher, approved=False, title="Pending One")

    def test_reader_sees_only_approved_articles(self):
        self.client.force_authenticate(self.reader)
        response = self.client.get(reverse("article-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a["title"] for a in response.data["results"]]
        self.assertIn("Approved One", titles)
        self.assertNotIn("Pending One", titles)

    def test_journalist_sees_own_pending_plus_all_approved(self):
        self.client.force_authenticate(self.journalist)
        response = self.client.get(reverse("article-list"))
        titles = [a["title"] for a in response.data["results"]]
        self.assertIn("Approved One", titles)
        self.assertIn("Pending One", titles)  # it's their own pending article

    def test_other_journalist_does_not_see_someone_elses_pending_article(self):
        self.client.force_authenticate(self.other_journalist)
        response = self.client.get(reverse("article-list"))
        titles = [a["title"] for a in response.data["results"]]
        self.assertIn("Approved One", titles)
        self.assertNotIn("Pending One", titles)

    def test_editor_sees_all_articles_including_pending(self):
        self.client.force_authenticate(self.editor)
        response = self.client.get(reverse("article-list"))
        titles = [a["title"] for a in response.data["results"]]
        self.assertIn("Approved One", titles)
        self.assertIn("Pending One", titles)


class ReaderSubscriptionTests(APITestCase):
    def setUp(self):
        ensure_groups()
        self.journalist_a = create_user("journoA", "JOURNALIST")
        self.journalist_b = create_user("journoB", "JOURNALIST")
        self.publisher_a = create_publisher("Publisher A", journalists=[self.journalist_a])
        self.publisher_b = create_publisher("Publisher B", journalists=[self.journalist_b])

        self.article_a = create_article(self.journalist_a, self.publisher_a, approved=True, title="From A")
        self.article_b = create_article(self.journalist_b, self.publisher_b, approved=True, title="From B")

        self.reader = create_user("subreader", "READER")
        self.reader.subscriptions_publishers.add(self.publisher_a)

    def test_subscribed_endpoint_returns_only_subscribed_publisher_articles(self):
        self.client.force_authenticate(self.reader)
        response = self.client.get(reverse("article-subscribed"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a["title"] for a in response.data["results"]] if "results" in response.data else [a["title"] for a in response.data]
        self.assertIn("From A", titles)
        self.assertNotIn("From B", titles)

    def test_subscribed_endpoint_includes_subscribed_journalist_independent_articles(self):
        independent = create_article(self.journalist_b, publisher=None, approved=True, title="Independent B")
        self.reader.subscriptions_journalists.add(self.journalist_b)
        self.client.force_authenticate(self.reader)
        response = self.client.get(reverse("article-subscribed"))
        data = response.data["results"] if "results" in response.data else response.data
        titles = [a["title"] for a in data]
        self.assertIn("Independent B", titles)

    def test_subscribed_endpoint_empty_when_no_subscriptions(self):
        lonely_reader = create_user("lonely", "READER")
        self.client.force_authenticate(lonely_reader)
        response = self.client.get(reverse("article-subscribed"))
        data = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(data), 0)


class ArticleCreateTests(APITestCase):
    def setUp(self):
        ensure_groups()
        self.journalist = create_user("creator", "JOURNALIST")
        self.reader = create_user("readerx", "READER")
        self.editor = create_user("editorx", "EDITOR")
        self.publisher = create_publisher(journalists=[self.journalist])

    def test_journalist_can_create_article(self):
        self.client.force_authenticate(self.journalist)
        payload = {"title": "Brand New", "content": "Fresh content.", "publisher": self.publisher.id}
        response = self.client.post(reverse("article-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        article = Article.objects.get(title="Brand New")
        self.assertEqual(article.author, self.journalist)
        self.assertFalse(article.approved)  # new articles start unapproved

    def test_reader_cannot_create_article(self):
        self.client.force_authenticate(self.reader)
        payload = {"title": "Should Fail", "content": "Nope."}
        response = self.client.post(reverse("article-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Article.objects.filter(title="Should Fail").exists())

    def test_journalist_cannot_publish_for_publisher_they_dont_belong_to(self):
        other_publisher = create_publisher("Other Pub")
        self.client.force_authenticate(self.journalist)
        payload = {"title": "Sneaky", "content": "...", "publisher": other_publisher.id}
        response = self.client.post(reverse("article-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ArticleEditorActionsTests(APITestCase):
    def setUp(self):
        ensure_groups()
        self.editor = create_user("approver", "EDITOR")
        self.journalist = create_user("writer", "JOURNALIST")
        self.reader = create_user("readery", "READER")
        self.publisher = create_publisher(journalists=[self.journalist])
        # Separate articles: one stays pending for the approve-flow tests,
        # one is approved up front for the delete/update permission tests
        # (so visibility isn't a confound - we're testing WRITE permission,
        # not read visibility, which is covered in ArticleListTests).
        self.pending_article = create_article(self.journalist, self.publisher, approved=False, title="Needs Review")
        self.article = create_article(self.journalist, self.publisher, approved=True, title="Already Live")

    def test_editor_can_approve_article(self):
        self.client.force_authenticate(self.editor)
        url = reverse("article-approve", kwargs={"pk": self.pending_article.pk})
        with patch("articles.signals.requests.post"):
            response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)
        self.assertEqual(self.pending_article.approved_by, self.editor)

    def test_journalist_cannot_approve_article(self):
        self.client.force_authenticate(self.journalist)
        url = reverse("article-approve", kwargs={"pk": self.pending_article.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_delete_article(self):
        self.client.force_authenticate(self.editor)
        url = reverse("article-detail", kwargs={"pk": self.article.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    def test_reader_cannot_delete_article(self):
        self.client.force_authenticate(self.reader)
        url = reverse("article-detail", kwargs={"pk": self.article.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Article.objects.filter(pk=self.article.pk).exists())

    def test_owning_journalist_can_update_own_article(self):
        self.client.force_authenticate(self.journalist)
        url = reverse("article-detail", kwargs={"pk": self.article.pk})
        response = self.client.put(url, {"title": "Updated Title", "content": "Updated."})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Updated Title")

    def test_other_journalist_cannot_update_someone_elses_article(self):
        outsider = create_user("outsider", "JOURNALIST")
        self.client.force_authenticate(outsider)
        url = reverse("article-detail", kwargs={"pk": self.article.pk})
        response = self.client.put(url, {"title": "Hijacked", "content": "..."})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
