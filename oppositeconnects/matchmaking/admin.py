from django.contrib import admin
from .models import BannedIP, UserProfile


@admin.register(BannedIP)
class BannedIPAdmin(admin.ModelAdmin):
    list_display  = ('ip_address', 'reason', 'banned_at')
    search_fields = ('ip_address',)
    list_filter   = ('banned_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'city', 'age')