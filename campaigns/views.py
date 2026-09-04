import inspect
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from campaigns.models import Campaign, Pitch
from campaigns.serializers import CampaignSerializer, PitchSerializer
from common import handle_error_log, ERROR_MSG


APP_NAME = "campaigns"


class CampaignListCreateView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        view_name = inspect.currentframe().f_code.co_name

        try:
            search = request.GET.get("search")

            campaigns = Campaign.objects.filter(user=request.user)

            if search:
                campaigns = campaigns.filter(
                    Q(name__icontains=search)
                    | Q(client_name__icontains=search)
                    | Q(brief__icontains=search)
                )

            serializer = CampaignSerializer(campaigns, many=True)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            handle_error_log(e=e, app_name=APP_NAME, view_name=view_name,)

            return Response({"error": ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR,)

    def post(self, request):
        view_name = inspect.currentframe().f_code.co_name

        try:
            serializer = CampaignSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST,)

            serializer.save(user=request.user)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CampaignDetailView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name

        try:
            campaign = Campaign.objects.get(pk=pk, user=request.user)

            serializer = CampaignSerializer(campaign)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name

        try:
            campaign = Campaign.objects.get(pk=pk, user=request.user)

            serializer = CampaignSerializer(
                campaign,
                data=request.data,
                partial=True,
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save(user=request.user)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name

        try:
            campaign = Campaign.objects.get(pk=pk, user=request.user)

            campaign.delete()

            return Response(
                status=status.HTTP_204_NO_CONTENT,
            )

        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PitchListCreateView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        view_name = inspect.currentframe().f_code.co_name

        try:
            campaign_id = request.GET.get("campaign")
            contact_id = request.GET.get("contact")
            generation_status = request.GET.get("generation_status")
            pitch_status = request.GET.get("status")

            pitches = Pitch.objects.select_related(
                "campaign",
                "contact",
            ).filter(
                campaign__user=request.user
            )

            if campaign_id:
                pitches = pitches.filter(
                    campaign_id=campaign_id
                )

            if contact_id:
                pitches = pitches.filter(
                    contact_id=contact_id
                )

            if generation_status:
                pitches = pitches.filter(
                    generation_status=generation_status
                )

            if pitch_status:
                pitches = pitches.filter(
                    status=pitch_status
                )

            serializer = PitchSerializer(
                pitches,
                many=True,
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            handle_error_log(e=e, app_name=APP_NAME, view_name=view_name,)

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        view_name = inspect.currentframe().f_code.co_name

        try:
            serializer = PitchSerializer(
                data=request.data,
                context={"request": request},
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PitchDetailView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name

        try:
            pitch = (
                Pitch.objects
                .select_related("campaign", "contact")
                .get(
                    pk=pk,
                    campaign__user=request.user,
                )
            )

            serializer = PitchSerializer(pitch)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Pitch.DoesNotExist:
            return Response(
                {"error": "Pitch not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name

        try:
            pitch = Pitch.objects.get(pk=pk, campaign__user=request.user)

            serializer = PitchSerializer(
                pitch,
                data=request.data,
                partial=True,
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except Pitch.DoesNotExist:
            return Response(
                {"error": "Pitch not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name

        try:
            pitch = Pitch.objects.get(pk=pk, campaign__user=request.user)

            pitch.delete()

            return Response(
                status=status.HTTP_204_NO_CONTENT,
            )

        except Pitch.DoesNotExist:
            return Response(
                {"error": "Pitch not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {"error": ERROR_MSG},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


campaign_list_create = CampaignListCreateView.as_view()
campaign_detail = CampaignDetailView.as_view()

pitch_list_create = PitchListCreateView.as_view()
pitch_detail = PitchDetailView.as_view()