"""
views for recipe apis
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe
from recipe import serializers

# modelviewset is set to work direclty with the model
class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database"""
    # use RecipeDetailSerializer since its most uused in several functions
    # if list is called at get_serializer_class fun then RecieSerailzer is called
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    # for one to access must go through tokenauth and also authenticated
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve the recipes for the authenticated user"""
        # filter the recipes only for the specific users in the system
        return self.queryset.filter(user=self.request.user).order_by('-id')

     # all occasions except for listing use RecipeDetailSerializer
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.RecipeSerializer

        return self.serializer_class

    # method inside a viewset in drf
    # serializer - serializer instance containign validated data client sent
    def perform_create(self, serializer):
        # associate the object created to the auth user
        serializer.save(user=self.request.user)