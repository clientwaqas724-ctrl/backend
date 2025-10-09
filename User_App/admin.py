from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User,QRScan,CustomerPoints
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email',
        'name',
        'phone',
        'role',
        'is_staff',
        'is_active',
        'created_at',
        'updated_at',
    )
    list_filter = ('role', 'is_staff', 'is_active', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone', 'profile_image')}),
        ('Role & Permissions', {
            'fields': (
                'role',
                'tc',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'name',
                'phone',
                'profile_image',
                'role',
                'tc',
                'password1',
                'password2',
                'is_active',
                'is_staff',
            ),
        }),
    )

    search_fields = ('email', 'name', 'phone')
    ordering = ('email',)
    readonly_fields = ('created_at', 'updated_at')
#######################################################################################################################################
###########################################################################################################
# QRScan Admin
###########################################################################################################
@admin.register(QRScan)
class QRScanAdmin(admin.ModelAdmin):
    list_display = ('customer', 'qr_code', 'points_awarded', 'scanned_at')
    list_filter = ('scanned_at',)
    search_fields = ('customer__email', 'qr_code')
    ordering = ('-scanned_at',)

###########################################################################################################
# CustomerPoints Admin
###########################################################################################################
@admin.register(CustomerPoints)
class CustomerPointsAdmin(admin.ModelAdmin):
    list_display = ('customer', 'total_points')
    search_fields = ('customer__email',)
    ordering = ('-total_points',)
##########################################################
# Register the custom user model with the custom admin
admin.site.register(User, CustomUserAdmin)
# ---- Custom Admin Site Titles ----
admin.site.site_header = "Customer_Loyalty_Platform – User Management"
admin.site.site_title = "Customer_Loyalty_Platform Admin"
admin.site.index_title = "Customer_Loyalty_Platform Administration"

