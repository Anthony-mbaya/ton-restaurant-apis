"""
views for user api
"""
# module - provide base class craeteapiview
from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    )

# CreateAPIView - handles post req for creating objs in db
class CreateUserView(generics.CreateAPIView):
    """create user"""
    # specify serializer to ber used in valiadtion
    serializer_class = UserSerializer

# obtaibauthtoken - validating user credentials and generating tokens.
class CreateTokenView(ObtainAuthToken):
    """create auth token for user"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """manage user account"""
    serializer_class = UserSerializer
    # how to know user is authenticated - token
    authentication_classes = [authentication.TokenAuthentication]
    # user known - but is allowed to do in the system
    permission_classes = [permissions.IsAuthenticated]

    # ovveride get req
    def get_object(self):
        """retrieve and return auth user"""
        # used in the serializer
        return self.request.user