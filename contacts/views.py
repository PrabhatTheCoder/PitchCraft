import inspect
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from common import handle_error_log, ERROR_MSG
from contacts.models import MediaContact
from contacts.serializers import MediaContactSerializer
 
APP_NAME = "contacts"
 

class MediaContactListCreateView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        view_name = inspect.currentframe().f_code.co_name

        try:
            search = request.GET.get("search")

            contacts = MediaContact.objects.filter(
                user=request.user,
                is_active=True,
            )

            if search:
                contacts = contacts.filter(
                    Q(name__icontains=search)
                    | Q(outlet__icontains=search)
                    | Q(beat__icontains=search)
                )

            serializer = MediaContactSerializer(
                contacts,
                many=True,
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
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

    def post(self, request):
        view_name = inspect.currentframe().f_code.co_name

        try:
            serializer = MediaContactSerializer(
                data=request.data
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
 
class MediaContactDetailView(APIView):
 
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
 
    def get(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name
 
        try:
            contact = MediaContact.objects.get(pk=pk, user=request.user, is_active=True,)
            serializer = MediaContactSerializer(contact)
 
            return Response(serializer.data, status=status.HTTP_200_OK)
 
        except MediaContact.DoesNotExist:
            return Response({"error": "Contact not found."}, status=status.HTTP_404_NOT_FOUND)
 
        except Exception as e:
            handle_error_log(e=e, app_name=APP_NAME, view_name=view_name)
            return Response({"error": ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
    def patch(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name
 
        try:
            contact = MediaContact.objects.get(pk=pk, user=request.user, is_active=True,)
            serializer = MediaContactSerializer(contact, data=request.data, partial=True)
 
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
            serializer.save(user=request.user)
 
            return Response(serializer.data, status=status.HTTP_200_OK)
 
        except MediaContact.DoesNotExist:
            return Response({"error": "Contact not found."}, status=status.HTTP_404_NOT_FOUND)
 
        except Exception as e:
            handle_error_log(e=e, app_name=APP_NAME, view_name=view_name)
            return Response({"error": ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
    def delete(self, request, pk):
        view_name = inspect.currentframe().f_code.co_name
 
        try:
            contact = MediaContact.objects.get(pk=pk, user=request.user, is_active=True,)
            # soft delete — pitches/history keep pointing at a real row
            contact.is_active = False
            contact.save(update_fields=["is_active", "updated_at"])
 
            return Response(status=status.HTTP_204_NO_CONTENT)
 
        except MediaContact.DoesNotExist:
            return Response({"error": "Contact not found."}, status=status.HTTP_404_NOT_FOUND)
 
        except Exception as e:
            handle_error_log(e=e, app_name=APP_NAME, view_name=view_name)
            return Response({"error": ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
