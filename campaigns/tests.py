from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from contacts.models import MediaContact

from .models import Campaign, Pitch
from .services import PitchGenerationError


class CampaignAPITests(APITestCase):
    def test_create_campaign(self):
        url = reverse("campaign-list")
        payload = {
            "name": "Series A Launch",
            "client_name": "Acme Robotics",
            "brief": "Acme closed a $10M Series A to build warehouse robots.",
            "tone": "bold",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Campaign.objects.count(), 1)


class GeneratePitchTests(APITestCase):
    def setUp(self):
        self.campaign = Campaign.objects.create(
            name="Series A Launch",
            client_name="Acme Robotics",
            brief="Acme closed a $10M Series A to build warehouse robots.",
        )
        self.contact = MediaContact.objects.create(
            name="Ada Lovelace",
            email="ada@example.com",
            outlet="The Analytical Engine Times",
            beat="robotics",
        )

    @patch("campaigns.views.generate_pitch")
    def test_generate_pitch_creates_pitch_record(self, mock_generate):
        mock_generate.return_value = {
            "subject": "Warehouse robots just got a $10M boost",
            "body": "Hi Ada, thought this might interest your robotics beat...",
        }
        url = reverse("pitch-generate")
        response = self.client.post(
            url, {"campaign_id": self.campaign.id, "contact_id": self.contact.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pitch.objects.count(), 1)
        pitch = Pitch.objects.first()
        self.assertEqual(pitch.subject, "Warehouse robots just got a $10M boost")
        self.assertEqual(pitch.status, Pitch.Status.DRAFT)

    @patch("campaigns.views.generate_pitch")
    def test_generate_pitch_is_idempotent_per_campaign_contact_pair(self, mock_generate):
        mock_generate.return_value = {"subject": "v1", "body": "v1 body"}
        url = reverse("pitch-generate")
        self.client.post(url, {"campaign_id": self.campaign.id, "contact_id": self.contact.id})

        mock_generate.return_value = {"subject": "v2", "body": "v2 body"}
        self.client.post(url, {"campaign_id": self.campaign.id, "contact_id": self.contact.id})

        self.assertEqual(Pitch.objects.count(), 1)
        self.assertEqual(Pitch.objects.first().subject, "v2")

    @patch("campaigns.views.generate_pitch")
    def test_generate_pitch_surfaces_ai_failure_as_502(self, mock_generate):
        mock_generate.side_effect = PitchGenerationError("boom")
        url = reverse("pitch-generate")
        response = self.client.post(
            url, {"campaign_id": self.campaign.id, "contact_id": self.contact.id}
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(Pitch.objects.count(), 0)

    def test_generate_pitch_requires_valid_ids(self):
        url = reverse("pitch-generate")
        response = self.client.post(url, {"campaign_id": 999, "contact_id": self.contact.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MarkSentTests(APITestCase):
    def test_mark_sent_updates_status(self):
        campaign = Campaign.objects.create(name="C", client_name="Acme", brief="b")
        contact = MediaContact.objects.create(name="Ada", email="ada@x.com", outlet="X")
        pitch = Pitch.objects.create(campaign=campaign, contact=contact, subject="s", body="b")

        url = reverse("pitch-mark-sent", args=[pitch.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pitch.refresh_from_db()
        self.assertEqual(pitch.status, Pitch.Status.SENT)
