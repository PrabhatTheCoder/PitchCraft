from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import MediaContact


class MediaContactModelTests(APITestCase):
    def test_str_representation(self):
        contact = MediaContact.objects.create(
            name="Ada Lovelace", email="ada@example.com", outlet="The Analytical Engine Times"
        )
        self.assertEqual(str(contact), "Ada Lovelace (The Analytical Engine Times)")


class MediaContactAPITests(APITestCase):
    def setUp(self):
        self.contact = MediaContact.objects.create(
            name="Ada Lovelace",
            email="ada@example.com",
            outlet="The Analytical Engine Times",
            beat="computing",
        )

    def test_list_contacts(self):
        url = reverse("contact-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_contact(self):
        url = reverse("contact-list")
        payload = {
            "name": "Grace Hopper",
            "email": "grace@example.com",
            "outlet": "Compiler Weekly",
            "beat": "programming languages",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MediaContact.objects.count(), 2)

    def test_create_contact_duplicate_email_rejected(self):
        url = reverse("contact-list")
        payload = {"name": "Dupe", "email": "ada@example.com", "outlet": "Somewhere"}
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_contacts_by_beat(self):
        url = reverse("contact-list")
        response = self.client.get(url, {"search": "computing"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        response = self.client.get(url, {"search": "sports"})
        self.assertEqual(response.data["count"], 0)
