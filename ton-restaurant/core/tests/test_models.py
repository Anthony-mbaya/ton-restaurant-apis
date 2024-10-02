"""
testing models
"""
from decimal import Decimal
# base class fro tests
from django.test import TestCase
# helper fun get default user model
from django.contrib.auth import get_user_model

from core import models

# helpe fun to create new user to be assigned
def create_user(email='test@example.com', password='testpass123'):
    """Create a new user"""
    return get_user_model().objects.create_user(email, password)

# use example.com - email
class ModelTests(TestCase):
    """creating user with email"""
    def test_create_user_wuth_email_successful(self):
        """test creating user with email is successful"""
        email = 'testemail@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password)) # check pass using hash system

    def test_new_user_email_normalized(self):
        """test the email for a new user is normalized"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email, expected_email in sample_emails:
            user = get_user_model().objects.create_user(email, 'smaplepass123')
            self.assertEqual(user.email, expected_email)

    def test_new_user_without_email_raises_error(self):
        """test that creating a user without an email raises an error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'testpass')

    def test_create_superuser(self):
        """test creating a superuser"""
        user = get_user_model().objects.create_superuser('test@example.com', 'testpass123')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """test creating a recipe is successful"""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('4.50'),
            description='Sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)

    # self - instance of the testcase
    def test_create_tag(self):
        # create new user obj using helper fun
        user = create_user()
        # create new tag in db using dj ORM - objeccts.create
        # tag fields - user, name
        tag = models.Tag.objects.create(user=user, name='Tag1')

        # str(tag) (which is the result of calling str() on the tag object) is equal to tag.name
        self.assertEqual(str(tag), tag.name)