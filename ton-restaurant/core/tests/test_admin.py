"""
test for django admin modification
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
# simulates a web browser. It allows you to make HTTP requests to your Django application
from django.test import Client


class AdminSiteTests(TestCase):
    """test fro django admin"""

    #  called before every individual test method to set up any state that is needed for the test.
    def setUp(self):
        """create a test user and client"""
        self.client = Client() # instanmce of Client - alolow make http req
        # create user with admin priviledges and store in self.admin_user
        self.admin_user = get_user_model().objects.create_superuser(
            email='adminuser@gmail.com',
            password='password123',
        )

        self.client.force_login(self.admin_user) # authenticate superuser without login form

        # create regular user - store in slef.user
        self.user = get_user_model().objects.create_user(
            email='testuser@gmail.com',
            password='testpass123',
            name='test user'
        )

    def test_users_list(self):
        """test that users are listed on the user page correclty"""
        # reverse - dj utility return url for given view name
        url = reverse('admin:core_user_changelist') # page of list of users
        res = self.client.get(url) # use test clint to perform GET for url above

        self.assertContains(res, self.user.name) # page contaoin name of e testuser defined
        self.assertContains(res, self.user.email) # contain email

    def test_edit_user_page(self):
        """test that the user edit page works correctly"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """test that the create user page works correctly"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)