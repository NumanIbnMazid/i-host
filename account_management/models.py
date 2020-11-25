
# from rest_framework import viewsets
from softdelete.models import SoftDeleteModel
import restaurant
from django.contrib.auth.base_user import BaseUserManager
from ihost.settings import TIME_ZONE
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
import uuid
from django.utils import timezone
from random import randint
from django.utils.timezone import timedelta
# Create your models here.


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        # if not username:
        #     raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(
            # username=username, email=email,
            **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)


class UserAccount(AbstractUser):
    USERS_IN_STATUS_CHOICES = [
        ("ACT", "Active"),
        ("UNV", "Unverified"),
        ("BLK", "Blacked"),
        ("DEL", "Deleted"),
    ]
    username = None
    email = None
    #first_name = None
    last_name = None

    # email = models.EmailField(max_length=35, null=True, blank=True)
    phone = models.CharField(max_length=35, unique=True)
    status = models.CharField(max_length=25,
                              choices=USERS_IN_STATUS_CHOICES, default='UNV')

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []
    objects = UserManager()

    # class Meta(AbstractUser.Meta):
    #     swappable = 'AUTH_USER_MODEL'


class CustomerInfo(models.Model):
    name = models.CharField(null=True, blank=True, max_length=250)
    email_address = models.EmailField(max_length=35, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    user = models.OneToOneField(to=UserAccount, on_delete=models.CASCADE)


class HotelStaffInformation(SoftDeleteModel):
    # user = models.ForeignKey()
    DAYS_OF_WEEK = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    )
    user = models.ForeignKey(
        to=UserAccount,  on_delete=models.CASCADE, related_name='hotel_staff')
    image = models.ImageField(null=True, blank=True)
    is_manager = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)
    is_waiter = models.BooleanField(default=False)
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    nid = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(null=True, blank=True, max_length=250)
    # shift_days = models.CharField(
    #     choices=DAYS_OF_WEEK, max_length=20, null=True, blank=True)
    restaurant = models.ForeignKey(
        to='restaurant.Restaurant', on_delete=models.CASCADE, null=True, blank=True, related_name='hotel_staff')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'restaurant'], name='staff_per_restaurant')
        ]


class PhoneVerification(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    phone = models.CharField(max_length=25)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    code_expired_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.phone.__str__()

    def generate_phone_verification(self):
        """ model method for generate verification code for a phone number.

        Attributes:
        verification_code: 6 digit random character
        code_expired_at:  3 minute expiry time of verification_code

        Returns:
        verification_code: newly created verification_code
        """
        self.verification_code = uuid.uuid4().time_mid.__str__() + \
            randint(0, 9).__str__()
        self.code_expired_at = timezone.now() + timedelta(minutes=3)
        self.save()
        return self.verification_code

    def verify_phone(self, code):
        """ model method for verify verification code for a phone number.

        Parameters:
        code: code to match with phone's verification code

        Attributes:
        verification_code: 6 digit random character

        Returns:
        str: error or success message
        """
        if TIME_ZONE.now() > self.code_expired_at:
            return "Verification Code Expired"
        elif code != self.verification_code:
            return "Wrong Verification Code"
        else:
            self.verification_code = " "
            self.save()
            return "Phone Verification Success"
