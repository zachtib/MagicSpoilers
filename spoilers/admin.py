from django.contrib import admin
from spoilers.models import MagicSet, MagicCard


class MagicCardInline(admin.TabularInline):
    model = MagicCard


@admin.register(MagicSet)
class MagicSetAdmin(admin.ModelAdmin):
    inlines = [MagicCardInline]
