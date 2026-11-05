from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import User
from .serializers import RegisterSerializer, SignInSerializer, UserSerializer


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfView(APIView):
    """Gives the frontend the CSRF cookie it must send back with sign-in."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


# DRF only checks CSRF for requests that are already signed in. Sign-in needs it
# too, or another site could silently sign a student into an attacker's account.
@method_decorator(csrf_protect, name='dispatch')
class SignInView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'sign_in'

    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=User.objects.normalize_email(serializer.validated_data['email']),
            password=serializer.validated_data['password'],
        )
        if user is None:
            # One message for every failure, so this endpoint cannot be used
            # to find out which emails have accounts.
            raise AuthenticationFailed('Invalid email or password.')

        login(request, user)  # also changes the session id, preventing session fixation
        return Response(UserSerializer(user).data)


# Protected for the same reason as sign-in: it also starts a session.
@method_decorator(csrf_protect, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class SignOutView(APIView):
    def post(self, request):
        logout(request)  # deletes the session on the server, not only the cookie
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
