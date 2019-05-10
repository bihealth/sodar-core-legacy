from django.contrib import admin
from .models import Project, Role, RoleAssignment, AppSetting, ProjectInvite


admin.site.register(Project)
admin.site.register(Role)
admin.site.register(RoleAssignment)
admin.site.register(AppSetting)
admin.site.register(ProjectInvite)
