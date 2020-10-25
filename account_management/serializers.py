from rest_framework import serializers
from .models import UserAccount


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ["phone", "password"]


class UserAccountPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        exclude = ["password"]


class UserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ['phone','first_name','last_name']
