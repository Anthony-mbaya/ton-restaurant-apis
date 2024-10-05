"""
test for ingredient api
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id] )

def create_user(email='example@email.com', password='testpass123'):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    def setUp(self):
        self.client  = APIClient()

    def test_auth_required(self):
        res  = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)\

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='milk')
        Ingredient.objects.create(user=self.user, name='flour')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """test list of ingredients limited to autrhenticated user only"""
        user2 = create_user(email='user2@example.com')
        # create ingred assigned to unauth user
        Ingredient.objects.create(user=user2, name='salt')
        # create ingred assigned to auth user
        ingredient = Ingredient.objects.create(user=self.user, name='pepper')
        # xcall ingredints for the auth useer
        res =  self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # created 2 ingredients but the one assigned to auth user is returned
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """test updating an ingredient"""
        # create new ingredient
        ingredient = Ingredient.objects.create(user=self.user, name='milk')

        payload = {'name': 'flour'}
        url = detail_url(ingredient.id)
        # make req
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting ingreditn"""
        ingredient = Ingredient.objects.create(user=self.user, name='Lettuce')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredient_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Apples')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Flour')
        recipe = Recipe.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('10.00'),
            user=self.user,
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        # create 2 ingredients 1 as var anfd the other on db
        ingredient = Ingredient.objects.create(user=self.user, name='Apples')
        Ingredient.objects.create(user=self.user, name='lentils')
        # create 2 recipews
        recipe1 = Recipe.objects.create(
            title='Apple Crumble',
            price=Decimal('11.00'),
            time_minutes=5,
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='Lentil Soup',
            price=Decimal('10.00'),
            time_minutes=5,
            user=self.user,
        )
        # adding ingredients to
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)