import inspect

from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from common import handle_error_log, ERROR_MSG

from users.serializers import (
    SignupSerializer,
    LoginSerializer,
)


APP_NAME = "users"


class SignupView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        view_name = inspect.currentframe().f_code.co_name

        try:
            serializer = SignupSerializer(
                data=request.data
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "user": SignupSerializer(user).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError:

            return Response(
                {
                    "error": "A user with this email already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
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


class LoginView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        view_name = inspect.currentframe().f_code.co_name

        try:
            serializer = LoginSerializer(
                data=request.data
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "user": SignupSerializer(user).data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
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


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    

    def post(self, request):

        view_name = inspect.currentframe().f_code.co_name

        try:
            refresh_token = request.data.get(
                "refresh"
            )

            if not refresh_token:
                return Response(
                    {
                        "error": "Refresh token is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response(
                {
                    "message": "Logout successful."
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:

            handle_error_log(
                e=e,
                app_name=APP_NAME,
                view_name=view_name,
            )

            return Response(
                {
                    "error": "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )