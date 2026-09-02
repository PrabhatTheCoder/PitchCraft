from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Campaign, Pitch
from .serializers import (
    CampaignSerializer,
    GeneratePitchRequestSerializer,
    PitchSerializer,
)
from .services import PitchGenerationError, generate_pitch


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer


class PitchViewSet(viewsets.ModelViewSet):
    """Pitches are normally created via /generate/, not by posting body text directly."""

    queryset = Pitch.objects.select_related("campaign", "contact").all()
    serializer_class = PitchSerializer

    @action(detail=False, methods=["post"])
    def generate(self, request):
        req = GeneratePitchRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        campaign = req.validated_data["campaign_id"]
        contact = req.validated_data["contact_id"]

        try:
            result = generate_pitch(campaign, contact)
        except PitchGenerationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        pitch, _ = Pitch.objects.update_or_create(
            campaign=campaign,
            contact=contact,
            defaults={"subject": result["subject"], "body": result["body"]},
        )
        return Response(PitchSerializer(pitch).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def mark_sent(self, request, pk=None):
        pitch = self.get_object()
        pitch.status = Pitch.Status.SENT
        pitch.save(update_fields=["status", "updated_at"])
        return Response(PitchSerializer(pitch).data)
