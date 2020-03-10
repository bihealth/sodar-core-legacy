"""REST API views for the samplesheets app"""

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
)

# Projectroles dependency
from projectroles.plugins import get_backend_api
from projectroles.views_api import CoreAPIGenericProjectMixin

from filesfolders.models import Folder
from filesfolders.serializers import (
    FolderSerializer,
    FileSerializer,
    HyperLinkSerializer,
)
from filesfolders.views import (
    FilesfoldersTimelineMixin,
    FileServeMixin,
    TL_OBJ_TYPES,
    APP_NAME,
)


class ListCreateAPITimelineMixin(FilesfoldersTimelineMixin):
    """
    Mixin that ties ListCreateAPIView:s to the SODAR timeline for filesfolders.
    """

    def perform_create(self, serializer):
        # Actually perform the creation
        super().perform_create(serializer)
        # Register creation with timeline
        self._add_item_modify_event(
            obj=serializer.instance, request=self.request, view_action='create'
        )


class RetrieveUpdateDestroyAPITimelineMixin(FilesfoldersTimelineMixin):
    """
    Mixin that ties RetrieveUpdateDestroyAPIView:s to the SODAR timeline for
    filesfolders.
    """

    def perform_update(self, serializer):
        # Collect update_attrs and old_data
        update_attrs = ['name', 'folder', 'description', 'flag']
        old_item = serializer.instance
        old_data = {}

        if old_item.__class__.__name__ == 'HyperLink':
            update_attrs.append('url')
        elif old_item.__class__.__name__ == 'File':
            update_attrs.append('public_url')

        for a in update_attrs:
            old_data[a] = getattr(old_item, a)

        # Actually perform the update
        super().perform_update(serializer)

        # Register update with timeline
        self._add_item_modify_event(
            obj=serializer.instance,
            request=self.request,
            view_action='update',
            update_attrs=update_attrs,
            old_data=old_data,
        )

    def perform_destroy(self, instance):
        instance.delete()

        timeline = get_backend_api('timeline_backend')

        # Add event in Timeline
        if timeline:
            obj_type = TL_OBJ_TYPES[instance.__class__.__name__]

            # Add event in Timeline
            tl_event = timeline.add_event(
                project=instance.project,
                app_name=APP_NAME,
                user=self.request.user,
                event_name='{}_delete'.format(obj_type),
                description='delete {} {{{}}}'.format(obj_type, obj_type),
                status_type='OK',
            )

            tl_event.add_object(
                obj=instance,
                label=obj_type,
                name=instance.get_path()
                if isinstance(instance, Folder)
                else instance.name,
            )


class ListCreatePermissionMixin:
    """Mixing adding get_permission_required() for list-create API views."""

    def get_permission_required(self):
        if self.request.method == 'POST':
            return 'filesfolders.add_data'

        else:
            return 'filesfolders.view_data'


class RetrieveUpdateDestroyPermissionMixin:
    """
    Mixing adding get_permission_required() for retrieve-update-destroy API
    views.
    """

    def get_permission_required(self):
        if self.request.method == 'GET':
            return 'filesfolders.view_data'

        else:
            obj = self.get_object()

            if obj.owner == self.request.user:
                return 'filesfolders.update_data_own'

            else:
                return 'filesfolders.update_data_all'


class FolderListCreateAPIView(
    ListCreateAPITimelineMixin,
    ListCreatePermissionMixin,
    CoreAPIGenericProjectMixin,
    ListCreateAPIView,
):
    """DRF list-create API view the Folder model."""

    serializer_class = FolderSerializer


class FolderRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPITimelineMixin,
    RetrieveUpdateDestroyPermissionMixin,
    CoreAPIGenericProjectMixin,
    RetrieveUpdateDestroyAPIView,
):
    """DRF retrieve-update-destroy API view for the Folder model."""

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'folder'
    serializer_class = FolderSerializer


class FileListCreateAPIView(
    ListCreateAPITimelineMixin,
    ListCreatePermissionMixin,
    CoreAPIGenericProjectMixin,
    ListCreateAPIView,
):
    """DRF list-create API view the File model."""

    serializer_class = FileSerializer


class FileRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPITimelineMixin,
    RetrieveUpdateDestroyPermissionMixin,
    CoreAPIGenericProjectMixin,
    RetrieveUpdateDestroyAPIView,
):
    """DRF retrieve-update-destroy API view for the File model."""

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'file'
    serializer_class = FileSerializer


class FileServeAPIView(
    CoreAPIGenericProjectMixin, FileServeMixin, GenericAPIView
):
    """Serve the file content."""

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'file'
    permission_required = 'filesfolders.view_data'


class HyperLinkListCreateAPIView(
    ListCreateAPITimelineMixin,
    ListCreatePermissionMixin,
    CoreAPIGenericProjectMixin,
    ListCreateAPIView,
):
    """DRF list-create API view the HyperLink model."""

    serializer_class = HyperLinkSerializer


class HyperLinkRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPITimelineMixin,
    RetrieveUpdateDestroyPermissionMixin,
    CoreAPIGenericProjectMixin,
    RetrieveUpdateDestroyAPIView,
):
    """DRF retrieve-update-destroy API view for the HyperLink model."""

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'hyperlink'
    serializer_class = HyperLinkSerializer
