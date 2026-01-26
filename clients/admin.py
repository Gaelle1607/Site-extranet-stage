from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Utilisateur


class UtilisateurInline(admin.StackedInline):
    model = Utilisateur
    can_delete = False
    verbose_name = 'Profil utilisateur'


class UserAdmin(BaseUserAdmin):
    inlines = (UtilisateurInline,)
    list_display = ('username', 'get_code_tiers', 'is_active')

    def get_code_tiers(self, obj):
        if hasattr(obj, 'utilisateur'):
            return obj.utilisateur.code_tiers
        return '-'
    get_code_tiers.short_description = 'Code tiers'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('code_tiers', 'user', 'actif')
    list_filter = ('actif',)
    search_fields = ('code_tiers', 'user__username')
