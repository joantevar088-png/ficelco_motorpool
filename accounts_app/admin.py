from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role', 'department', 'phone', 'profile_pic')}),
    )
    list_display = ('username', 'email', 'role', 'department', 'is_staff')
    list_filter = ('role', 'department', 'is_staff')


admin.site.register(CustomUser, CustomUserAdmin)