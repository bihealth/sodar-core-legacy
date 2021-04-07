"""REST API view model serializers for the projectroles app"""

from email.utils import parseaddr

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import exceptions, serializers
from drf_keyed_list import KeyedListSerializer

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    ProjectInvite,
    SODAR_CONSTANTS,
)
from projectroles.utils import build_secret, get_expiry_date
from projectroles.views import (
    ProjectModifyMixin,
    RoleAssignmentModifyMixin,
    ProjectInviteMixin,
)


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']


# Local constants
REMOTE_MODIFY_MSG = (
    'Modification of remote projects is not allowed, modify on '
    'the SOURCE site instead'
)

User = get_user_model()


# Base Serializers -------------------------------------------------------------


class SODARModelSerializer(serializers.ModelSerializer):
    """Base serializer for any SODAR model with a sodar_uuid field"""

    sodar_uuid = serializers.CharField(read_only=True)

    class Meta:
        pass

    def to_representation(self, instance):
        """
        Override to_representation() to ensure sodar_uuid is included for object
        creation POST responses.
        """
        ret = super().to_representation(instance)
        if 'sodar_uuid' not in ret and 'sodar_uuid' in self.context:
            ret['sodar_uuid'] = str(self.context['sodar_uuid'])
        return ret

    def save(self, **kwargs):
        """
        Override save() to ensure sodar_uuid is included for object creation
        POST responses.
        """
        obj = super().save(**kwargs)
        return self.post_save(obj)

    def post_save(self, obj):
        """
        Function to call at the end of a custom save() method. Ensures the
        returning of sodar_uuid in object creation POST responses.

        :param obj: Object created in save()
        :return: obj
        """
        if hasattr(obj, 'sodar_uuid'):
            self.context['sodar_uuid'] = obj.sodar_uuid
        return obj


class SODARProjectModelSerializer(SODARModelSerializer):
    """
    Base serializer for SODAR models with a project relation.

    The project field is read only because it is retrieved through the object
    reference in the URL.
    """

    project = serializers.SlugRelatedField(
        slug_field='sodar_uuid', read_only=True
    )

    class Meta:
        pass

    def to_representation(self, instance):
        """
        Override to_representation() to ensure the project value is included
        in responses.
        """
        ret = super().to_representation(instance)
        if 'project' not in ret and 'project' in self.context:
            ret['project'] = str(self.context['project'].sodar_uuid)
        return ret

    def create(self, validated_data):
        """Override create() to add project into validated data"""
        if 'project' not in validated_data and 'project' in self.context:
            validated_data['project'] = self.context['project']
        return super().create(validated_data)


class SODARNestedListSerializer(SODARModelSerializer):
    """
    Serializer to display nested SODAR models as dicts with sodar_uuid as key.
    """

    class Meta:
        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'sodar_uuid'
        duplicate_list_key = True  # Extension to drf-keyed-list

    def to_representation(self, instance):
        """
        Override to_representation() to pop project from a nested list
        representation, where the project context is already known in the
        topmost model.
        """
        ret = super().to_representation(instance)
        if self.context.get('project'):
            ret.pop('project', None)
        return ret


class SODARUserSerializer(SODARModelSerializer):
    """Serializer for the user model used in SODAR Core based sites"""

    class Meta:
        model = User
        fields = ['username', 'name', 'email', 'sodar_uuid']


# Projectroles Serializers -----------------------------------------------------


class RoleAssignmentValidateMixin:
    """Mixin for common role assignment validation"""

    def validate(self, attrs):
        project = self.context['project']
        current_user = self.context['request'].user
        del_limit = getattr(settings, 'PROJECTROLES_DELEGATE_LIMIT', 1)

        # Validation for remote sites and projects
        if project.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)

        if 'role' not in attrs:
            return attrs

        # Do not allow modifying/inviting owner
        if attrs['role'].name == PROJECT_ROLE_OWNER:
            raise serializers.ValidationError('Modifying owner not allowed')

        # Check delegate perms
        if attrs[
            'role'
        ].name == PROJECT_ROLE_DELEGATE and not current_user.has_perm(
            'projectroles.update_project_delegate', project
        ):
            raise exceptions.PermissionDenied(
                'User lacks permission to assign delegates'
            )

        # Check delegate limit
        if (
            attrs['role'].name == PROJECT_ROLE_DELEGATE
            and del_limit != 0
            and project.get_delegates(exclude_inherited=True).count()
            >= del_limit
        ):
            raise serializers.ValidationError(
                'Project delegate limit of {} has been reached'.format(
                    del_limit
                )
            )

        return attrs


class RoleAssignmentSerializer(
    RoleAssignmentModifyMixin,
    RoleAssignmentValidateMixin,
    SODARProjectModelSerializer,
):
    """Serializer for the RoleAssignment model"""

    role = serializers.SlugRelatedField(
        slug_field='name', queryset=Role.objects.all()
    )
    user = serializers.SlugRelatedField(
        slug_field='sodar_uuid', queryset=User.objects.all()
    )

    class Meta:
        model = RoleAssignment
        fields = ['project', 'role', 'user', 'sodar_uuid']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        project = self.context['project']

        # Do not allow updating user
        if (
            self.instance
            and 'user' in attrs
            and attrs['user'] != self.instance.user
        ):
            raise serializers.ValidationError(
                'Updating the user is not allowed, create a new role '
                'assignment instead'
            )

        # Check for existing role if creating
        if not self.instance:
            old_as = RoleAssignment.objects.filter(
                project=project, user=attrs['user']
            ).first()

            if old_as:
                raise serializers.ValidationError(
                    'User already has the role of "{}" in project '
                    '(UUID={})'.format(old_as.role.name, old_as.sodar_uuid)
                )

        # Add user to instance for PATCH requests
        if self.instance and not attrs.get('user'):
            attrs['user'] = self.instance.user

        return attrs

    def save(self, **kwargs):
        """Override save() to handle saving locally or through Taskflow"""
        # NOTE: Role not updated in response data unless we set self.instance
        # TODO: Figure out a clean fix
        self.instance = self.post_save(
            self.modify_assignment(
                data=self.validated_data,
                request=self.context['request'],
                project=self.context['project'],
                instance=self.instance,
            )
        )
        return self.instance


class RoleAssignmentNestedListSerializer(
    SODARNestedListSerializer, RoleAssignmentSerializer
):
    """Nested list serializer for the RoleAssignment model."""

    user = SODARUserSerializer(read_only=True)

    class Meta(SODARNestedListSerializer.Meta):
        model = RoleAssignment
        fields = ['role', 'user', 'sodar_uuid']
        read_only_fields = ['role']


class ProjectInviteSerializer(
    ProjectInviteMixin, RoleAssignmentValidateMixin, SODARProjectModelSerializer
):
    """Serializer for the ProjectInvite model"""

    issuer = SODARUserSerializer(read_only=True)
    role = serializers.SlugRelatedField(
        slug_field='name', queryset=Role.objects.all()
    )

    class Meta:
        model = ProjectInvite
        fields = [
            'email',
            'project',
            'role',
            'issuer',
            'date_created',
            'date_expire',
            'message',
            'sodar_uuid',
        ]
        read_only_fields = ['issuer', 'date_created', 'date_expire', 'active']

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Validate email
        if not parseaddr(attrs['email'])[1]:
            raise serializers.ValidationError(
                'Invalid email address "{}"'.format(attrs['email'])
            )

        # Check for existing user
        user = User.objects.filter(email=attrs['email']).first()
        if user:
            raise serializers.ValidationError(
                'User already exist in system with given email '
                '"{}": {} ({})'.format(
                    attrs['email'], user.username, user.sodar_uuid
                )
            )

        return attrs

    def create(self, validated_data):
        validated_data['issuer'] = self.context['request'].user
        validated_data['date_expire'] = get_expiry_date()
        validated_data['secret'] = build_secret()
        return super().create(validated_data)

    def save(self, **kwargs):
        obj = super().save(**kwargs)
        self.handle_invite(obj, self.context['request'], add_message=False)
        return self.post_save(obj)


class ProjectSerializer(ProjectModifyMixin, SODARModelSerializer):
    """Serializer for the Project model"""

    owner = serializers.CharField(write_only=True)
    parent = serializers.SlugRelatedField(
        slug_field='sodar_uuid',
        many=False,
        allow_null=True,
        queryset=Project.objects.filter(type=PROJECT_TYPE_CATEGORY),
    )
    readme = serializers.CharField(required=False, allow_blank=True)
    roles = RoleAssignmentNestedListSerializer(read_only=True, many=True)

    class Meta:
        model = Project
        fields = [
            'title',
            'type',
            'parent',
            'description',
            'readme',
            'public_guest_access',
            'submit_status',
            'owner',
            'roles',
            'sodar_uuid',
        ]
        read_only_fields = ['submit_status']

    def validate(self, attrs):
        site_mode = getattr(
            settings,
            'PROJECTROLES_SITE_MODE',
            SODAR_CONSTANTS['SITE_MODE_SOURCE'],
        )
        target_create = getattr(settings, 'PROJECTROLES_TARGET_CREATE', True)
        disable_categories = getattr(
            settings, 'PROJECTROLES_DISABLE_CATEGORIES', False
        )
        current_user = self.context['request'].user

        # Validation for remote sites and projects
        if self.instance and self.instance.is_remote():
            raise serializers.ValidationError(REMOTE_MODIFY_MSG)
        elif (
            not self.instance
            and site_mode == SODAR_CONSTANTS['SITE_MODE_TARGET']
            and not target_create
        ):
            raise serializers.ValidationError(
                'Creation of local projects not allowed on this target site'
            )

        # Validate parent
        parent = attrs.get('parent')

        # Attempting to move project under category without perms
        if (
            parent
            and not current_user.is_superuser
            and not current_user.has_perm('projectroles.create_project', parent)
            and (not self.instance or self.instance.parent != parent)
        ):
            raise exceptions.PermissionDenied(
                'User lacks permission to place project under given category'
            )

        if parent and parent.type != PROJECT_TYPE_CATEGORY:
            raise serializers.ValidationError('Parent is not a category')

        elif (
            'parent' in attrs
            and not parent
            and self.instance
            and self.instance.parent
            and not current_user.is_superuser
        ):
            raise exceptions.PermissionDenied(
                'Only superusers are allowed to place categories in root'
            )

        # Attempting to create/move project in root
        if (
            'parent' in attrs
            and not parent
            and attrs.get('type') == PROJECT_TYPE_PROJECT
            and not disable_categories
        ):
            raise serializers.ValidationError(
                'Project must be placed under a category'
            )

        # Ensure we are not moving a category under one of its children
        if (
            parent
            and self.instance
            and self.instance.type == PROJECT_TYPE_CATEGORY
            and parent in self.instance.get_children(flat=True)
        ):
            raise serializers.ValidationError(
                'Moving a category under its own child is not allowed'
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
            if (
                self.partial
                and attrs['owner'] != self.instance.get_owner().user.sodar_uuid
            ):
                raise serializers.ValidationError(
                    'Modifying owner not allowed here, '
                    'use ownership transfer API view instead'
                )
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
        # NOTE: post_save() not needed here since we do an atomic model.save()
        return self.modify_project(
            data=self.validated_data,
            request=self.context['request'],
            instance=self.instance,
        )

    def to_representation(self, instance):
        """Override to make sure fields are correctly returned."""
        ret = super().to_representation(instance)
        parent = ret.get('parent')
        project = Project.objects.get(
            title=ret['title'],
            **{'parent__sodar_uuid': parent} if parent else {},
        )
        # TODO: Better way to ensure this?
        ret['readme'] = project.readme.raw or ''
        if not ret.get('sodar_uuid'):
            ret['sodar_uuid'] = str(project.sodar_uuid)
        return ret
