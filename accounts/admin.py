from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Profile, ActivityLog, AuditLog

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    verbose_name_plural = 'Profile Settings'
    readonly_fields = ['financial_health_score', 'ai_insights_cache']
    fieldsets = (
        (None, {
            'fields': ('avatar', 'preferred_currency', 'dark_mode', 'phone_number')
        }),
        ('Dynamic Aggregates', {
            'classes': ('collapse',),
            'fields': ('financial_health_score', 'ai_insights_cache'),
        }),
    )

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_email_verified_status', 'is_active_status', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'is_email_verified')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['lock_accounts', 'unlock_accounts', 'reset_passwords']

    # Include email on the "Add User" form (required by custom User model)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    # Include custom fields on the "Change User" form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Verification', {'fields': ('is_email_verified', 'email_verification_token')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def save_formset(self, request, form, formset, change):
        # The Profile is auto-created by the post_save signal on User as soon as
        # the user is saved above. If the admin also filled in the inline Profile
        # form on the "Add user" page, formset.save() would try to INSERT a brand
        # new Profile row for the same user and crash with a UNIQUE constraint
        # error (accounts_profile.user_id). Copy the submitted field values onto
        # the already-existing Profile instead of inserting a duplicate row.
        if formset.model is Profile:
            editable_fields = ('avatar', 'preferred_currency', 'dark_mode', 'phone_number')
            instances = formset.save(commit=False)
            for instance in instances:
                existing = Profile.objects.filter(user=instance.user).first()
                if existing:
                    for field in editable_fields:
                        setattr(existing, field, getattr(instance, field))
                    existing.save()
                else:
                    instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            formset.save_m2m()
        else:
            formset.save()

    @admin.display(description='Email Verified')
    def is_email_verified_status(self, obj):
        if obj.is_email_verified:
            return format_html('<span style="color: #10b981; font-weight: bold;">&#10004; Verified</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">&#10008; Unverified</span>')

    @admin.display(description='Account Status')
    def is_active_status(self, obj):
        if obj.is_active:
            return format_html('<span style="background-color: #d1fae5; color: #065f46; padding: 3px 8px; border-radius: 12px; font-size: 11px;">Active</span>')
        return format_html('<span style="background-color: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 12px; font-size: 11px;">Locked</span>')

    # Bulk User Actions
    @admin.action(description='Lock selected accounts')
    def lock_accounts(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        self.message_user(request, f"{rows_updated} user accounts were locked.")

    @admin.action(description='Unlock selected accounts')
    def unlock_accounts(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        self.message_user(request, f"{rows_updated} user accounts were unlocked.")

    @admin.action(description='Reset passwords (default: TemporaryPass123)')
    def reset_passwords(self, request, queryset):
        for u in queryset:
            u.set_password('TemporaryPass123')
            u.save()
        self.message_user(request, f"Password reset to 'TemporaryPass123' for {queryset.count()} users.")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_currency', 'dark_mode', 'phone_number', 'financial_health_score')
    list_filter = ('preferred_currency', 'dark_mode')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('financial_health_score', 'ai_insights_cache')
    ordering = ('-financial_health_score',)
    list_per_page = 25

    def has_add_permission(self, request):
        # Profiles are auto-created by the User post_save signal
        return False

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'user_agent', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action', 'ip_address')
    readonly_fields = ('user', 'action', 'ip_address', 'user_agent', 'timestamp')
    ordering = ('-timestamp',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'action')
    readonly_fields = ('user', 'model_name', 'object_id', 'action', 'changes', 'timestamp')
    ordering = ('-timestamp',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
