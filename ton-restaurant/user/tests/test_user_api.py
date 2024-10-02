"""
Tests for the user API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

# user - app, create - endpoint
CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

# allow any dict contains details that passed in user
def create_user(**params):
    return get_user_model().objects.create_user(**params)


# public class - unauthenticated class
#              - registering user
class PublicUserApiTests(TestCase):
    """Test the users API (public)"""
    def setUp(self):
        self.client = APIClient() # simulates dj rest apis req

    def test_create_user_success(self):
        """Test creating a new user with a valid payload is successful"""
        # WHEN VALID PAYLOAD (email,pass, nm) to creation endpoint - api creates successful
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }

        # make post req and pass payload - content(payload ) passed to the url(CREATE_USERT_UR;L)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # retrieve user object from provide payload using email
        user = get_user_model().objects.get(email=payload['email'])
        # check pass match of payload and retrieved user
        self.assertTrue(user.check_password(payload['password']))
        # res.data - data returned in res to user creation
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """error from creating user with existing email"""
        # existing email
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_short_error(self):
        """Test that a short password returns an error"""
        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test User',
            }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # check user exists
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        # confirm user does not exixts in db
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user."""
        user_details = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }

        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test that the token is not created with invalid credentials"""
        create_user(email='test@example.com', password='goodpas')

        payload = {
            'email': 'test@example.com',
            'password':'badpas'
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_pass(self):
        """Test that the token is not created with blank password"""
        payload = {
            'email': 'test@example.com',
            'password': ''
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data) # ensure no token returned
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# private class
class PrivateUserApiTests(TestCase):
    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test name',
        )
        self.client = APIClient()
        # any req made is authentcated
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed on the me endpoint."""
        # disable post on me endpoint
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""
        # payload to update user(authenticated setup)
        payload = {
            'name': 'New name',
            'password': 'newpassword123',
        }
        # send patch request to me endpoint
        res = self.client.patch(ME_URL, payload)
        # refresh form db for user values to be updated
        self.user.refresh_from_db()
        # check if user values have been updated
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        # check if status code is 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)