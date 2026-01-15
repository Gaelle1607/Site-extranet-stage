from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Client


class ClientInline(admin.StackedInline):
    model = Client
    can_delete = False
    verbose_name = 'Profil client'


class UserAdmin(BaseUserAdmin):
    inlines = (ClientInline,)
    list_display = ('username', 'get_nom', 'is_active')

    def get_nom(self, obj):
        if hasattr(obj, 'client'):
            return obj.client.nom
        return '-'
    get_nom.short_description = 'Nom'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'user', 'actif')
    list_filter = ('actif',)
    search_fields = ('nom', 'user__username')
