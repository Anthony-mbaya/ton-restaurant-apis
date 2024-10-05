"""
db models
"""
import uuid
import os

from django.conf import settings
from django.db import models
# AbstarctBaseUser - contain functionality of auth system
# Permissionmmixinb  - contain functionality for permisiions and fields
# bauser
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

# helper fun - determine where to path to stor image
def recipe_image_file_path(instance, filename):
    """generate file path for new recipe image"""
    # take file name and extraxt the extension
    ext = os.path.splitext(filename)[1]
    # create own name by appending the exreacted extension eg png, jpg
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'recipe', filename)

# user manager
class UserManager(BaseUserManager):
    """manager for users"""
    def create_user(self, email, password=None, **extra_fields):
        """create, save and return a new user"""
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields) # self.model since base user is accociated
        user.set_password(password) # after creating user hash thwe pass
        user.save(using=self._db) # support adding multiple db's

        return user

    def create_superuser(self, email, password):
        """create and return a superuser"""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# create custom user model - user
class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using email instead of username"""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) # if one can login to django admin

    objects = UserManager() # assign user manager

    # replace default field that came with dj user model
    USERNAME_FIELD = 'email'

# Model - base class simple model
class Recipe(models.Model):
    """Recipe object"""
    # create relationship between  models using FK
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    # add tag
    # manytomany since have more tags in more recipes
    # any of tag or recipe can be associated with each other
    tags = models.ManyToManyField('Tag')
    ingredients = models.ManyToManyField('Ingredient')
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self):
        return self.title


class Tag(models.Model):
    """Tag object"""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    """Ingredient object"""
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name