from django.contrib import admin

from spoilers.models import MagicSet, MagicCard


class MagicCardInline(admin.TabularInline):
    model = MagicCard


@admin.register(MagicSet)
class MagicSetAdmin(admin.ModelAdmin):
    inlines = [MagicCardInline]
    list_display = ('name', 'code', 'release_date', 'watched')
    list_filter = ('release_date', 'watched')
    search_fields = ['name', 'code']
