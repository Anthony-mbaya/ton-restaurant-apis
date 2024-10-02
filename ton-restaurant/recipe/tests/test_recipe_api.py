"""
test for recipe apis
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')
# constructs a URL that includes the recipe's unique identifier (recipe_id
# recipe detail url as fun since will have unique id
def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])

# helper function
def create_recipe(user, **params):
    """create and return sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.50'),
        'description': 'Sample recipe for testing',
        'link': 'http://example.com/recipe.pdf',
    }
    # if params are provided gets updated
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

# helper fun to avoid recreating user
def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """test unauthenticated recipe api access"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test that authentication is required"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """test authenticated recipe api access"""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """test retrieving a list of recipes"""
        # create 2 recipes
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        # get the response - both recipes returned since created by same auth user
        res = self.client.get(RECIPES_URL)

        # query the db to retrieve all recipe objects order
        recipes = Recipe.objects.all().order_by('-id')
        # pass list of items
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """test retrieving a list of recipes is limited to authenticated user"""
        """other_user = get_user_model().objects.create_user(
            'other@example.com',
            'passother123',
        )"""
        other_user = create_user(email='other@example.com', password='passother123')
        create_recipe(user=other_user)
        create_recipe(user=self.user) # auth user

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        # create and assign recipe to user
        recipe = create_recipe(user=self.user)

        # create detail url - using id
        url = detail_url(recipe.id)
        # get the response
        res = self.client.get(url)
        # serialize without many = true
        serializer = RecipeDetailSerializer(recipe)
        # check result of client is same as serializer
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        # use payloads to ensure holding of data to be passed
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': Decimal('5.99')
        }
        # post
        res = self.client.post(RECIPES_URL, payload)
        # compare the status code to match with created status code
        # print(res.data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # get the created recipe by ist id
        recipe = Recipe.objects.get(id=res.data['id'])
        # check the recipe data
        # k = keys = fieldnames, v = values = new or expected vals
        # .items() - fun returning key-val pairs
        # loop iterates through each key-val pair
        # getattr - fynalically get value of attribute of obj eg. if k=key = 'title then recipe.title
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user = self.user,
            title='Sample Recipe',
            link=original_link,
        )
        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        # patch
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe',
            link='https://example.com/recipe.pdf',
            description='sample recipe description',
        )
        payload = {
            'title': 'New recipe title',
            'time_minutes': 20,
            'price': Decimal('3.99'),
            'description': 'New recipe description',
            'link': 'https://example.com/new-recipe.pdf',
        }
        url = detail_url(recipe.id)
        # put
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        # loop through @ value provided in the payload
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        new_user = create_user(
            email='newuser@example.com',
            password='password123',
        )
        # create recipe with existing user
        recipe = create_recipe(user=self.user)

        payload = {
            'user': new_user.id
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        new_user = create_user(
            email='newuser@example.com',
            password='password123',
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())