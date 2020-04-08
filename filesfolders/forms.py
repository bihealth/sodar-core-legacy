from zipfile import ZipFile

from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat

from db_file_storage.form_widgets import DBClearableFileInput

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import SODARModelForm
from projectroles.models import Project
from projectroles.utils import build_secret

from .models import File, Folder, HyperLink


# Settings
MAX_UPLOAD_SIZE = settings.FILESFOLDERS_MAX_UPLOAD_SIZE
MAX_ARCHIVE_SIZE = settings.FILESFOLDERS_MAX_ARCHIVE_SIZE

# Local constants
APP_NAME = 'filesfolders'


app_settings = AppSettingAPI()


class FilesfoldersItemForm(SODARModelForm):
    """Base form for Filesfolders item creation/updating"""

    def __init__(
        self, current_user=None, folder=None, project=None, *args, **kwargs
    ):
        """Override for form initialization"""
        super().__init__(*args, **kwargs)

        self.current_user = None
        self.project = None
        self.folder = None

        # Get current user for checking permissions for form items
        if current_user:
            self.current_user = current_user

        if folder:
            self.folder = Folder.objects.get(sodar_uuid=folder)
            self.project = self.folder.project

        elif project:
            self.project = Project.objects.get(sodar_uuid=project)

        # Modify ModelChoiceFields to use sodar_uuid
        self.fields['folder'].to_field_name = 'sodar_uuid'


class FolderForm(FilesfoldersItemForm):
    """Form for Folder creation/updating"""

    class Meta:
        model = Folder
        fields = ['name', 'folder', 'flag', 'description']

    def __init__(
        self, current_user=None, folder=None, project=None, *args, **kwargs
    ):
        """Override for form initialization"""
        super().__init__(
            current_user=current_user,
            project=project,
            folder=folder,
            *args,
            **kwargs
        )

        # Creation
        if not self.instance.pk:
            # Don't allow changing folder if we are creating a new object
            self.initial['folder'] = (
                self.folder.sodar_uuid if self.folder else None
            )
            self.fields['folder'].widget = forms.HiddenInput()

        # Updating
        else:
            # Allow moving folder inside other folders in project
            folder_choices = [(None, 'root')]

            folders = Folder.objects.filter(
                project=self.instance.project.pk
            ).exclude(pk=self.instance.pk)

            # Exclude everything under current folder
            folders = [f for f in folders if not f.has_in_path(self.instance)]

            for f in folders:
                folder_choices.append((f.sodar_uuid, f.get_path()))

            self.fields['folder'].choices = folder_choices
            self.initial['folder'] = (
                self.instance.folder.sodar_uuid
                if self.instance.folder
                else None
            )

    def clean(self):
        # Creation
        if not self.instance.pk:
            try:
                Folder.objects.get(
                    project=self.project,
                    folder=self.folder,
                    name=self.cleaned_data['name'],
                )

                self.add_error('name', 'Folder already exists')

            except Folder.DoesNotExist:
                pass

        # Updating
        else:
            # Ensure a folder with the same name does not exist in the location
            old_folder = None

            try:
                old_folder = Folder.objects.get(pk=self.instance.pk)

            except Folder.DoesNotExist:
                pass

            if old_folder and (
                old_folder.name != self.cleaned_data['name']
                or old_folder.folder != self.cleaned_data['folder']
            ):
                try:
                    Folder.objects.get(
                        project=self.instance.project,
                        folder=self.cleaned_data['folder'],
                        name=self.cleaned_data['name'],
                    )

                    self.add_error('name', 'Folder already exists')

                except Folder.DoesNotExist:
                    pass

        return self.cleaned_data

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)

        # Updating
        if self.instance.pk:
            obj.owner = self.instance.owner
            obj.project = self.instance.project
            obj.folder = self.instance.folder

        # Creation
        else:
            obj.owner = self.current_user
            obj.project = self.project

            if self.folder:
                obj.folder = self.folder

        obj.save()
        return obj


class FileForm(FilesfoldersItemForm):
    """Form for File creation/updating"""

    unpack_archive = forms.BooleanField(
        required=False, label='Extract files from archive'
    )

    class Meta:
        model = File
        fields = [
            'file',
            'unpack_archive',
            'folder',
            'description',
            'flag',
            'public_url',
        ]
        widgets = {'file': DBClearableFileInput}
        help_texts = {
            'file': 'Uploaded file (maximum size: {})'.format(
                filesizeformat(MAX_UPLOAD_SIZE)
            )
        }

    @staticmethod
    def _get_file_size(file):
        try:
            return file.size

        except NotImplementedError:
            return file.file.size

    def _check_size(self, file_size, limit):
        if file_size > limit:
            self.add_error(
                'file',
                'File too large, maximum size is {} bytes '
                '(file size is {} bytes)'.format(limit, file_size),
            )
            return False
        return True

    def __init__(
        self, current_user=None, folder=None, project=None, *args, **kwargs
    ):
        """Override for form initialization"""
        super().__init__(
            current_user=current_user,
            folder=folder,
            project=project,
            *args,
            **kwargs
        )

        if self.instance.pk:
            self.project = self.instance.project

        # Disable public URL creation if setting is false
        if not app_settings.get_app_setting(
            APP_NAME, 'allow_public_links', project=self.project
        ):
            self.fields['public_url'].disabled = True

        # Creation
        if not self.instance.pk:
            # Don't allow changing folder if we are creating a new object
            self.initial['folder'] = (
                self.folder.sodar_uuid if self.folder else None
            )
            self.fields['folder'].widget = forms.HiddenInput()
            self.fields['file'].required = True

        # Updating
        else:
            # Allow moving file inside other folders in project
            folder_choices = [(None, 'root')]

            for f in Folder.objects.filter(project=self.instance.project.pk):
                folder_choices.append((f.sodar_uuid, f.get_path()))

            self.fields['folder'].choices = folder_choices
            self.initial['folder'] = (
                self.instance.folder.sodar_uuid
                if self.instance.folder
                else None
            )

    def clean(self):
        project = self.instance.project if self.instance.pk else self.project
        folder = self.cleaned_data.get('folder')
        file = self.cleaned_data.get('file')
        if not file:
            return self.cleaned_data

        unpack_archive = self.cleaned_data.get('unpack_archive')
        new_filename = file.name.split('/')[-1]
        size = self._get_file_size(file)

        # Normal file handling
        if file and (
            not hasattr(file, 'content_type')
            or file.content_type
            not in ['application/zip', 'application/x-zip-compressed']
        ):
            # Ensure max file size is not exceeded
            if not self._check_size(size, MAX_UPLOAD_SIZE):
                return self.cleaned_data

            # Attempting to unpack a non-zip file
            if unpack_archive:
                self.add_error(
                    'unpack_archive',
                    'Attempting to extract from a file that is not a '
                    'Zip archive',
                )
                return self.cleaned_data

        # Zip archive handling
        elif unpack_archive:
            # Ensure max archive size is not exceeded
            if not self._check_size(size, MAX_ARCHIVE_SIZE):
                return self.cleaned_data

            try:
                zip_file = ZipFile(file)

            except Exception as ex:
                self.add_error('file', 'Unable to open zip file: {}'.format(ex))
                return self.cleaned_data

            archive_files = [f for f in zip_file.infolist() if not f.is_dir()]

            if len(archive_files) == 0:
                self.add_error(
                    'file', 'Found nothing to extract from zip archive'
                )
                return self.cleaned_data

            for f in archive_files:
                # Ensure file size
                if not self._check_size(f.file_size, MAX_UPLOAD_SIZE):
                    return self.cleaned_data

                # Check if any of the files exist
                path_split = f.filename.split('/')
                check_folder = folder

                for p in path_split[:-1]:
                    # Advance in path
                    check_folder = Folder.objects.filter(
                        name=p, folder=check_folder
                    ).first()

                # Once reached the correct path, check if file exists
                if File.objects.filter(
                    name=path_split[-1], folder=check_folder
                ).first():
                    self.add_error(
                        'file', 'File already exists: {}'.format(f.filename)
                    )
                    return self.cleaned_data

        # Creation
        if (
            not self.instance.pk
            and not unpack_archive
            and File.objects.filter(
                project=project, folder=self.folder, name=file.name
            ).first()
        ):
            self.add_error('file', 'File already exists')

        # Updating
        elif self.instance.pk:
            # Ensure file with the same name does not exist in the same
            # folder (unless we update file with the same folder and name)
            old_file = File.objects.filter(
                project=self.instance.project,
                folder=self.instance.folder,
                name=self.instance.name,
            ).first()

            if (
                old_file
                and self.instance.name != str(file)
                and File.objects.filter(
                    project=self.instance.project, folder=folder, name=file
                ).first()
            ):
                self.add_error('file', 'File already exists')

            # Moving:
            # If moving, ensure an identical file doesn't exist in the
            # target folder
            if (
                self.instance.folder != folder
                and File.objects.filter(
                    project=self.instance.project,
                    folder=folder,
                    name__in=[new_filename, self.instance.name],
                ).count()
                > 0
            ):
                self.add_error(
                    'folder',
                    'File with identical name already exists in folder',
                )

        return self.cleaned_data

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)

        # Creation
        if not self.instance.pk:
            obj.name = obj.file.name
            obj.owner = self.current_user
            obj.project = self.project

            if self.folder:
                obj.folder = self.folder

            obj.secret = build_secret()  # Secret string created here

        # Updating
        else:
            old_file = File.objects.get(pk=self.instance.pk)

            if old_file.file != self.instance.file:
                obj.file = self.instance.file
                obj.name = obj.file.name.split('/')[-1]

            obj.owner = self.instance.owner
            obj.project = self.instance.project

            if app_settings.get_app_setting(
                APP_NAME, 'allow_public_links', project=self.instance.project
            ):
                obj.public_url = self.instance.public_url

            else:
                obj.public_url = False

            obj.secret = self.instance.secret

            if self.instance.folder:
                obj.folder = self.instance.folder

        obj.save()
        return obj


class HyperLinkForm(FilesfoldersItemForm):
    """Form for HyperLink creation/updating"""

    class Meta:
        model = HyperLink
        fields = ['name', 'url', 'folder', 'flag', 'description']

    def __init__(
        self, current_user=None, folder=None, project=None, *args, **kwargs
    ):
        """Override for form initialization"""
        super().__init__(
            current_user=current_user,
            project=project,
            folder=folder,
            *args,
            **kwargs
        )

        # Creation
        if not self.instance.pk:
            # Don't allow changing folder if we are creating a new object
            self.initial['folder'] = (
                self.folder.sodar_uuid if self.folder else None
            )
            self.fields['folder'].widget = forms.HiddenInput()

        # Updating
        else:
            # Allow moving file inside other folders in project
            folder_choices = [(None, 'root')]

            for f in Folder.objects.filter(project=self.instance.project.pk):
                folder_choices.append((f.sodar_uuid, f.get_path()))

            self.fields['folder'].choices = folder_choices
            self.initial['folder'] = (
                self.instance.folder.sodar_uuid
                if self.instance.folder
                else None
            )

    def clean(self):
        # Creation
        if not self.instance.pk:
            try:
                HyperLink.objects.get(
                    project=self.project,
                    folder=self.folder,
                    name=self.cleaned_data['name'],
                )
                self.add_error('name', 'Link already exists')

            except HyperLink.DoesNotExist:
                pass

        # Updating
        else:
            # Ensure a link with the same name does not exist in the location
            old_link = None

            try:
                old_link = HyperLink.objects.get(pk=self.instance.pk)

            except HyperLink.DoesNotExist:
                pass

            if old_link and (
                old_link.name != self.cleaned_data['name']
                or old_link.folder != self.cleaned_data['folder']
            ):
                try:
                    HyperLink.objects.get(
                        project=self.instance.project,
                        folder=self.cleaned_data['folder'],
                        name=self.cleaned_data['name'],
                    )

                    self.add_error('name', 'Link already exists')

                except HyperLink.DoesNotExist:
                    pass

        return self.cleaned_data

    def save(self, *args, **kwargs):
        """Override of form saving function"""
        obj = super().save(commit=False)

        # Updating
        if self.instance.pk:
            obj.owner = self.instance.owner
            obj.project = self.instance.project
            obj.folder = self.instance.folder

        # Creation
        else:
            obj.owner = self.current_user
            obj.project = self.project

            if self.folder:
                obj.folder = self.folder

        obj.save()
        return obj
