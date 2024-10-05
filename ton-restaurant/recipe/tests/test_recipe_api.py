"""
test for recipe apis
"""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Recipe, Tag, Ingredient, )

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPES_URL = reverse('recipe:recipe-list')
# constructs a URL that includes the recipe's unique identifier (recipe_id
# recipe detail url as fun since will have unique id
def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """create and return image upload url"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

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


    # creating recipes with tags
    def test_create_recipe_with_new_tags(self):
        payload = {
            'title': 'New Recipe',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'tag1'}, {'name': 'tag2'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        tag_kenyan = Tag.objects.create(user=self.user, name='Kenyan')
        payload = {
            'title': 'Ugandan',
            'time_minutes': 4,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Kenyan'}, {'name': 'Tanzanian'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_kenyan, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'Lunch'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        # create recipe wityh auth user
        recipe = create_recipe(user=self.user)
        # add breakfast tag to the recipe
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    # creating ingrtedient
    def test_create_recipe_with_new_ingredient(self):
        """creating recipe with new ingredient"""
        payload = {
            'title': 'Test recipe',
            'time_minutes': 10,
            'price': Decimal('5.00'),
            'ingredients': [{'name': 'milk'}, {'name': 'salt'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """creating recipe with existing ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='lemon')
        payload = {
            'title': 'Kenyan soup',
            'time_minutes': 10,
            'price': Decimal('5.00'),
            'ingredients': [{'name': 'lemon'}, {'name': 'fish soucer'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """creating ingredient on update"""
        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'limes'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='limes')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_existing_ingredient(self):
        """update recipe assign ingredient"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='chilli')
        payload = {'ingredients': [{'name': 'chilli'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """test clearinmg ingredints"""
        ingredient = Ingredient.objects.create(user=self.user, name='garlic')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    # test filterign by tags
    def test_filter_by_tags(self):
        """test filtering by tags"""
        recipe1 = create_recipe(user=self.user, title='Cake')
        recipe2 = create_recipe(user=self.user, title='Ugali')
        tag1 = Tag.objects.create(user=self.user, name='Kenyan food')
        tag2 = Tag.objects.create(user=self.user, name='Tanzanian food')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = create_recipe(user=self.user, title='Ugandan')

        params = {'tags': f'{tag1.id}, {tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    # test filterign by ingredients
    def test_filter_by_ingredients(self):
        """test filtering by ingredints"""
        recipe1 = create_recipe(user=self.user, title='chicken')
        recipe2 = create_recipe(user=self.user, title='matoke')
        ingredient1 = Ingredient.objects.create(user=self.user, name='salt')
        ingredient2 = Ingredient.objects.create(user=self.user, name='milk')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = create_recipe(user=self.user, title='cheese')

        params = {'ingredients': f'{ingredient1.id}, {ingredient2.id}'}
        res = self.client.get(RECIPES_URL, params)

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


# test images upload
class ImageUploadTests(TestCase):
    """tests for image upload api"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    # runs after every test - delete image creayed
    def tearDown(self):
        """delete recipe after each test"""
        self.recipe.image.delete()

    def test_upload_image(self):
        """test uploading an image to a recipe"""
        # create url
        url = image_upload_url(self.recipe.id)
        # create temporary files
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            # send request
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'bad image'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)