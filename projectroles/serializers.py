"""API view model serializers for the projectroles app"""

from django.contrib.auth import get_user_model

from rest_framework import serializers
from drf_keyed_list import KeyedListSerializer

from projectroles.models import Project, RoleAssignment


User = get_user_model()


# Base Serializers -------------------------------------------------------------


class SODARModelSerializer(serializers.ModelSerializer):
    """Base serializer for any SODAR model with a sodar_uuid field"""

    sodar_uuid = serializers.CharField(read_only=True)

    class Meta:
        pass


class SODARNestedListSerializer(SODARModelSerializer):
    """Serializer for SODAR models in nested lists. To be used in cases where
    the object is not intended to be listed or modified on its own."""

    class Meta:
        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'sodar_uuid'


# Projectroles Serializers -----------------------------------------------------


class SODARUserSerializer(SODARModelSerializer):
    """Serializer for the user model used in the SODAR Core based site"""

    class Meta:
        model = User
        fields = ['username', 'name', 'email', 'sodar_uuid']


class RoleAssignmentNestedListSerializer(SODARNestedListSerializer):
    """List serializer for the RoleAssignment model"""

    user = SODARUserSerializer(read_only=True, many=False)
    role = serializers.ReadOnlyField(source='role.name')

    class Meta(SODARNestedListSerializer.Meta):
        model = RoleAssignment
        fields = ['user', 'role', 'sodar_uuid']


class ProjectSerializer(SODARModelSerializer):
    """Serializer for the Project model"""

    parent = serializers.SerializerMethodField()
    readme = serializers.CharField(source='readme.raw')
    roles = RoleAssignmentNestedListSerializer(read_only=True, many=True)

    class Meta:
        model = Project
        fields = [
            'title',
            'type',
            'parent',
            'description',
            'readme',
            'submit_status',
            'roles',
            'sodar_uuid',
        ]
        read_only_fields = ['submit_status']

    def get_parent(self, obj):
        if obj.parent:
            return obj.parent.sodar_uuid
