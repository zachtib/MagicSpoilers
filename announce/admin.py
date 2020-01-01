# Register your models here.
from django.contrib import admin

from announce.models import Channel


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    pass
