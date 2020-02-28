"""API view model serializers for the projectroles app"""

from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers
from drf_keyed_list import KeyedListSerializer

from projectroles.models import Project, RoleAssignment, SODAR_CONSTANTS
from projectroles.views import ProjectModifyMixin


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']


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

    role = serializers.ReadOnlyField(source='role.name')
    user = SODARUserSerializer(read_only=True, many=False)

    class Meta(SODARNestedListSerializer.Meta):
        model = RoleAssignment
        fields = ['user', 'role', 'sodar_uuid']


class ProjectSerializer(ProjectModifyMixin, SODARModelSerializer):
    """Serializer for the Project model"""

    owner = serializers.CharField(write_only=True)
    parent = serializers.SerializerMethodField(read_only=True)
    readme = serializers.CharField(required=False)
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
            'owner',
            'roles',
            'sodar_uuid',
        ]
        read_only_fields = ['submit_status']

    def get_parent(self, obj):
        if isinstance(obj, (dict, OrderedDict)) and obj.get('parent'):
            return obj['parent'].sodar_uuid

        elif isinstance(obj, Project) and obj.parent:
            return str(obj.parent.sodar_uuid)

    def validate(self, attrs):
        # Validate and set parent
        parent_uuid = self.context.get('project')
        parent = None

        # Parent found
        if parent_uuid:
            parent = Project.objects.filter(sodar_uuid=parent_uuid).first()

            if not parent:
                raise serializers.ValidationError('Parent category not found')

            if parent and parent.type != PROJECT_TYPE_CATEGORY:
                raise serializers.ValidationError('Parent is not a category')

        #  Attempting to create project in root
        elif (
            attrs['type'] == PROJECT_TYPE_PROJECT
            and not parent_uuid
            and not settings.PROJECTROLES_DISABLE_CATEGORIES
        ):
            raise serializers.ValidationError(
                'Project must be placed under a category'
            )

        attrs['parent'] = parent

        # Validate title
        if parent and attrs['title'] == parent.title:
            raise serializers.ValidationError('Title can\'t match with parent')

        if Project.objects.filter(title=attrs['title'], parent=parent):
            raise serializers.ValidationError(
                'Title must be unique within parent'
            )

        # Validate type
        if attrs['type'] not in [PROJECT_TYPE_CATEGORY, PROJECT_TYPE_PROJECT]:
            raise serializers.ValidationError(
                'Type is not {} or {}'.format(
                    PROJECT_TYPE_CATEGORY, PROJECT_TYPE_PROJECT
                )
            )

        # Validate and set owner
        owner = User.objects.filter(sodar_uuid=attrs['owner']).first()

        if not owner:
            raise serializers.ValidationError('Owner not found')

        attrs['owner'] = owner

        # Set readme
        if 'readme' in attrs and 'raw' in attrs['readme']:
            attrs['readme'] = attrs['readme']['raw']

        return attrs

    def save(self, **kwargs):
        """Override save() to handle saving locally or through Taskflow"""
        return self.modify_project(
            data=self.validated_data,
            request=self.context['request'],
            instance=self.instance,
        )

    def to_representation(self, instance):
        """
        Override to make sure sodar_uuid is correctly returned: upon creation
        the (required) atomic save() within modify_project() causes no UUID
        to appear.
        """
        representation = super().to_representation(instance)

        if not representation.get('sodar_uuid'):
            parent = representation.get('parent')

            if parent:
                project = Project.objects.get(
                    title=representation['title'], parent__sodar_uuid=parent
                )

            else:
                project = Project.objects.get(
                    title=representation['title'], parent=None
                )

            representation['sodar_uuid'] = str(project.sodar_uuid)

        return representation
