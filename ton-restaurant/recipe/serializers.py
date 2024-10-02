"""
serializers for recipe api
"""
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            'id',
            'title',
            'time_minutes',
            'price',
            'link',
        ]
        read_only_fields = ['id']


# RecipeSerializer as base class to help in extension and add extra fields
class RecipeDetailSerializer(RecipeSerializer):
    # use meta class inside the RecipeSerializer - GET META values provided
    class Meta(RecipeSerializer.Meta):
        # take existing fields and add descr
        fields = RecipeSerializer.Meta.fields + ['description']