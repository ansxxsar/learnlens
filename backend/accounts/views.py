from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.http import FileResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import User
from . import photos
from .serializers import (
    ChangePasswordSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    SignInSerializer,
    UserSerializer,
)


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

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class ProfilePhotoView(APIView):
    """The signed-in user's own photo. There is no user id in the URL, so one
    user can never request another user's photo."""

    parser_classes = [MultiPartParser]
    throttle_scope = 'profile_photo'

    def get_throttles(self):
        return [ScopedRateThrottle()] if self.request.method == 'PUT' else []

    def get(self, request):
        photo = request.user.photo
        if not photo or not photo.storage.exists(photo.name):
            raise Http404
        response = FileResponse(photo.open('rb'), content_type='image/jpeg')
        response['Cache-Control'] = 'private, max-age=86400'
        return response

    def put(self, request):
        # Checked before request.data is read, so an oversized upload is refused
        # without being parsed. The multipart wrapper adds a little to the size.
        if int(request.META.get('CONTENT_LENGTH') or 0) > photos.MAX_PHOTO_BYTES + 64 * 1024:
            raise ValidationError({'photo': [photos.TOO_LARGE_MESSAGE]})

        uploaded = request.data.get('photo')
        if uploaded is None or isinstance(uploaded, str):
            raise ValidationError({'photo': ['Choose an image file.']})

        photos.save_profile_photo(request.user, uploaded)
        return Response(UserSerializer(request.user).data)

    def delete(self, request):
        photos.remove_profile_photo(request.user)
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'change_password'

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        # Keeps this session signed in. Sessions on other devices stop working.
        update_session_auth_hash(request, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
