# energy/permissions.py
from rest_framework import permissions


class IsDeviceOwner(permissions.BasePermission):
    """
    Permette l'accesso solo ai proprietari del dispositivo o agli admin
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.plant.owner == request.user


class ReadOnly(permissions.BasePermission):
    """
    Permette solo operazioni di lettura
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Permette operazioni di scrittura solo allo staff
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
