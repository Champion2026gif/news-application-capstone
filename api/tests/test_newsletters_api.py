from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from articles.models import Newsletter

from .factories import create_article, create_publisher, create_user, ensure_groups


class NewsletterAPITests(APITestCase):
    def setUp(self):
        ensure_groups()
        self.journalist = create_user("newsjourno", "JOURNALIST")
        self.editor = create_user("newseditor", "EDITOR")
        self.reader = create_user("newsreader", "READER")
        self.publisher = create_publisher(journalists=[self.journalist])
        self.approved_article = create_article(self.journalist, self.publisher, approved=True, title="Feature Story")

    def test_journalist_can_create_newsletter(self):
        self.client.force_authenticate(self.journalist)
        payload = {"title": "Weekly Roundup", "description": "This week's picks.", "articles": [self.approved_article.id]}
        response = self.client.post(reverse("newsletter-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        newsletter = Newsletter.objects.get(title="Weekly Roundup")
        self.assertEqual(newsletter.author, self.journalist)
        self.assertIn(self.approved_article, newsletter.articles.all())

    def test_editor_can_create_and_edit_newsletter(self):
        self.client.force_authenticate(self.editor)
        response = self.client.post(reverse("newsletter-list"), {"title": "Editor's Pick", "description": "Curated."})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        newsletter_id = response.data["id"]

        response = self.client.put(
            reverse("newsletter-detail", kwargs={"pk": newsletter_id}),
            {"title": "Editor's Pick (Updated)", "description": "Curated and revised."},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reader_can_view_but_not_create_newsletter(self):
        self.client.force_authenticate(self.reader)
        newsletter = Newsletter.objects.create(title="Public NL", description="", author=self.journalist)

        list_response = self.client.get(reverse("newsletter-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        create_response = self.client.post(reverse("newsletter-list"), {"title": "Should Fail", "description": ""})
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reader_cannot_delete_newsletter(self):
        newsletter = Newsletter.objects.create(title="Protected", description="", author=self.journalist)
        self.client.force_authenticate(self.reader)
        response = self.client.delete(reverse("newsletter-detail", kwargs={"pk": newsletter.pk}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
