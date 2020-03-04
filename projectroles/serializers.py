"""API view model serializers for the projectroles app"""

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import exceptions, serializers
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
    # parent = serializers.CharField(allow_blank=True, allow_null=True)
    parent = serializers.SlugRelatedField(
        slug_field='sodar_uuid',
        many=False,
        allow_null=True,
        queryset=Project.objects.filter(type=PROJECT_TYPE_CATEGORY),
    )
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

    def validate(self, attrs):
        user = self.context['request'].user

        # Validate parent
        parent = attrs.get('parent')

        # Attempting to move project under category without perms
        if (
            parent
            and not user.is_superuser
            and not user.has_perm('projectroles.create_project', parent)
            and (not self.instance or self.instance.parent != parent)
        ):
            raise exceptions.PermissionDenied(
                'User lacks permission to place project under given category'
            )

        if parent and parent.type != PROJECT_TYPE_CATEGORY:
            raise serializers.ValidationError('Parent is not a category')

        # Attempting to create/move project in root
        elif (
            attrs.get('type') == PROJECT_TYPE_PROJECT
            and not parent
            and not settings.PROJECTROLES_DISABLE_CATEGORIES
        ):
            raise serializers.ValidationError(
                'Project must be placed under a category'
            )

        # Validate type
        if (
            attrs.get('type')
            and self.instance
            and attrs['type'] != self.instance.type
        ):
            raise serializers.ValidationError(
                'Changing the project type is not allowed'
            )

        # Validate title
        if parent and attrs.get('title') == parent.title:
            raise serializers.ValidationError('Title can\'t match with parent')

        if (
            attrs.get('title')
            and not self.instance
            and Project.objects.filter(title=attrs['title'], parent=parent)
        ):
            raise serializers.ValidationError(
                'Title must be unique within parent'
            )

        # Validate type
        if attrs.get('type') not in [
            PROJECT_TYPE_CATEGORY,
            PROJECT_TYPE_PROJECT,
            None,
        ]:  # None is ok for PATCH (will be updated in modify_project())
            raise serializers.ValidationError(
                'Type is not {} or {}'.format(
                    PROJECT_TYPE_CATEGORY, PROJECT_TYPE_PROJECT
                )
            )

        # Validate and set owner
        if attrs.get('owner'):
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
        Override to make sure fields are correctly returned.
        """
        representation = super().to_representation(instance)
        parent = representation.get('parent')
        project = Project.objects.get(
            title=representation['title'],
            **{'parent__sodar_uuid': parent} if parent else {},
        )

        # TODO: Better way to ensure this?
        representation['readme'] = project.readme.raw or ''

        if not representation.get('sodar_uuid'):
            representation['sodar_uuid'] = str(project.sodar_uuid)

        return representation
