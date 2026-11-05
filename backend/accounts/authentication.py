from rest_framework.authentication import SessionAuthentication


class SessionAuth(SessionAuthentication):
    """Session auth that answers anonymous requests with 401 instead of 403.

    DRF only sends 401 when the auth class names a challenge. The frontend needs
    the difference: 401 means "sign in", 403 means "signed in but not allowed".
    """

    def authenticate_header(self, request):
        return 'Session'
