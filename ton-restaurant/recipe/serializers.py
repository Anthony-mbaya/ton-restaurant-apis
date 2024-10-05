"""
serializers for recipe api
"""
from rest_framework import serializers

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)


class IngredientSerializer(serializers.ModelSerializer):
    """serializer for ingredients"""
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_field = ['id']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)
    class Meta:
        model = Recipe
        fields = [
            'id',
            'title',
            'time_minutes',
            'price',
            'link',
            'tags',
            'ingredients',
        ]
        read_only_fields = ['id']
    #  internal methosd = start with _
    def _get_or_create_tags(self, tags_data, recipe):
        """Helper method to get or create existing tags"""
        auth_user = self.context['request'].user
        for tag in tags_data:
            tag_obj, created = Tag.objects.get_or_create(user=auth_user, **tag)
            recipe.tags.add(tag_obj)
    # this method not be used outside serializer
    def _get_or_create_ingredients(self, ingredients_data, recipe):
        """handle getting or creating ingredients"""
        auth_user = self.context['request'].user
        for ingredient in ingredients_data:
            ingredient_obj, created = Ingredient.objects.get_or_create(user=auth_user, **ingredient)
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        # rm tag/ingedient from valiadated data and assign to varible tag_data,ingredient_data
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])
        # exluding tag_data will used to create a new recipe
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags_data, recipe)
        self._get_or_create_ingredients(ingredients_data, recipe)

        return recipe

    def update(self, instance, validated_data):
        # rm tags/ingredients from valiadetd data
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        if tags_data is not None:
            # if value associated to tags then clear
            instance.tags.clear()
            self._get_or_create_tags(tags_data, instance)
        if ingredients_data is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients_data, instance)

        # Update the recipe's attributes (like title, price
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

# RecipeSerializer as base class to help in extension and add extra fields
class RecipeDetailSerializer(RecipeSerializer):
    # use meta class inside the RecipeSerializer - GET META values provided
    class Meta(RecipeSerializer.Meta):
        # take existing fields and add descr
        fields = RecipeSerializer.Meta.fields + ['description', 'image']

# separate api to handle image upload
class RecipeImageSerializer(serializers.ModelSerializer):
    """serializer for uploading images to recipes"""
    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}