"""
serializers for user api view
"""
from django.contrib.auth import (
    get_user_model,
    authenticate,
    )
from django.utils.translation import gettext_lazy as _
# serializers - convert objects to/fro py data types
# 1. take JSON input from API - VALDATES - convert to py object otr model
from rest_framework import serializers

# modelserializer allow valiadtion and save to specific model definned
class UserSerializer(serializers.ModelSerializer):
    """Serializer for user object"""

    class Meta:
        model = get_user_model() # only return user model
        # fileds user able to change by api
        fields = ['email', 'password', 'name'] # filds to be saved in model
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
                }
                }

    def create(self, validated_data):
        """Create and return a new user"""
        # override create - handle hashing
        return get_user_model().objects.create_user(**validated_data)

    # instance - existing user obj to update
    # validated data - dict with data to update
    def update(self, instance, validated_data):
        """Update a user, setting the password correctly and return it"""
        # override update - handle hashing - get pass and rm it
        # if pass not provide default is none
        password = validated_data.pop('password', None)
        # allow update of non pass fields
        user = super().update(instance, validated_data)

        # popped out pass will be hashed here
        if password:
            user.set_password(password)
            user.save()

        return user

# used for custom validation
class AuthTokenSerializer(serializers.Serializer):
    """serializer for the user auth token"""
    email = serializers.EmailField() # valid email address
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    # valiadet input to serializer from view
    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email') # get email passed at endpoint
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email, # email is username
            password=password,
        )
        # if user is not None - return user
        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authorization')
        attrs['user'] = user
        return attrs
