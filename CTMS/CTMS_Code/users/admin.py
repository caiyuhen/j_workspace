from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import User

class CustomUserAdmin(UserAdmin, SimpleHistoryAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_verified')
    list_filter = ('role', 'is_verified')
    fieldsets = UserAdmin.fieldsets + (
        ('CTMS Info', {'fields': ('role', 'organization', 'phone_number', 'is_verified')}),
    )

admin.site.register(User, CustomUserAdmin)
