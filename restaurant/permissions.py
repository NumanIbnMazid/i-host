from django.db.models import Q
from restaurant.models import Restaurant
from account_management.models import HotelStaffInformation, UserAccount
from rest_framework import permissions

"""
[summary]
        # self.check_object_permissions(request, obj=1) #its restaurant_id

Returns
-------
[type]
    [description]
"""


class IsRestaurantOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    message = 'Not a restaurant owner.'

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if not bool(request.user and request.user.is_authenticated):
            return False

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            user=request.user, is_owner=True)
        if hotel_staff_qs:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if not bool(request.user and request.user.is_authenticated):
            return False

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            restaurant=obj, user=request.user, is_owner=True)
        if hotel_staff_qs:
            return True
        else:
            return False


class IsRestaurantManager(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    message = 'Not a restaurant manager.'

    # def has_permission(self, request, view):
    #     """
    #     Return `True` if permission is granted, `False` otherwise.
    #     """

    #     return False
    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """

        if not bool(request.user and request.user.is_authenticated):
            return False
        hotel_staff_qs = HotelStaffInformation.objects.filter(
            user=request.user, is_manager=True)
        if hotel_staff_qs:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if not bool(request.user and request.user.is_authenticated):
            return False

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            restaurant=obj, user_id=request.user.pk, is_manager=True)
        if hotel_staff_qs:
            return True
        else:
            return False


class IsRestaurantWaiter(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    message = 'Not a restaurant waiter.'

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if not bool(request.user and request.user.is_authenticated):
            return False

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            user=request.user, is_waiter=True)
        if hotel_staff_qs:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if not bool(request.user and request.user.is_authenticated):
            return False

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            restaurant=obj, user=request.user, is_waiter=True)
        if hotel_staff_qs:
            return True
        else:
            return False


class IsRestaurantStaff(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    message = 'Not a restaurant staff.'

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if not bool(request.user and request.user.is_authenticated):
            return False

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            Q(user=request.user), Q(is_waiter=True) | Q(is_owner=True) | Q(is_manager=True))
        if hotel_staff_qs:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # hotel_staff_qs = HotelStaffInformation.objects.filter(
        #     restaurant=obj, user=request.user, is_waiter=True)
        if not bool(request.user and request.user.is_authenticated):
            return False

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            Q(user=request.user, restaurant=obj), Q(is_waiter=True) | Q(is_owner=True) | Q(is_manager=True))

        if hotel_staff_qs:
            return True
        else:
            return False


class IsRestaurantManagementOrAdmin(permissions.IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    message = 'Not a restaurant staff.'

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if not bool(request.user and request.user.is_authenticated):
            return False

        if request.user.is_staff or request.user.is_superuser:
            return True
        hotel_staff_qs = HotelStaffInformation.objects.filter(
            Q(user=request.user), Q(is_owner=True) | Q(is_manager=True) | Q(user__is_staff=True) | Q(user__is_superuser=True))
        if hotel_staff_qs:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # hotel_staff_qs = HotelStaffInformation.objects.filter(
        #     restaurant=obj, user=request.user, is_waiter=True)

        if not bool(request.user and request.user.is_authenticated):
            return False

        if UserAccount.objects.filter(Q(is_staff=True) | Q(is_superuser=True), pk=request.user.pk):
            return True

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            Q(user=request.user, restaurant=obj),   Q(is_owner=True) | Q(is_manager=True))

        if hotel_staff_qs:
            return True
        else:
            return False


class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    message = 'Not a restaurant staff.'

    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            return False

        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if request.user.is_staff or request.user.is_superuser:
            return True
        hotel_staff_qs = HotelStaffInformation.objects.filter(
            Q(user=request.user), Q(is_owner=True) | Q(user__is_staff=True) | Q(user__is_superuser=True))
        if hotel_staff_qs:
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # hotel_staff_qs = HotelStaffInformation.objects.filter(
        #     restaurant=obj, user=request.user, is_waiter=True)
        if not bool(request.user and request.user.is_authenticated):
            return False

        if UserAccount.objects.filter(Q(is_staff=True) | Q(is_superuser=True), pk=request.user.pk):
            return True

        hotel_staff_qs = HotelStaffInformation.objects.filter(
            Q(user=request.user, restaurant=obj),   Q(is_owner=True))

        if hotel_staff_qs:
            return True
        else:
            return False
