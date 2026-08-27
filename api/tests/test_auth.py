"""
Authentication tests: verify the JWT token endpoint works and that
unauthenticated requests are rejected.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import create_user, ensure_groups


class AuthenticationTests(APITestCase):
    def setUp(self):
        ensure_groups()
        self.reader = create_user("reader1", "READER")

    def test_obtain_token_with_valid_credentials(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"username": "reader1", "password": "testpass123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_with_invalid_credentials_fails(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"username": "reader1", "password": "wrongpass"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_request_to_articles_is_rejected(self):
        url = reverse("article-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
