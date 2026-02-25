from django.contrib import admin

from .models import (
    AuditLog,
    Axis,
    ChangeRequest,
    City,
    InfrastructureFeature,
    Institution,
    Layer,
    NewsPost,
    Province,
    SupportTicket,
    UserProfile,
)


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_type", "contact_email")
    search_fields = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "scope", "scope_value", "institution")
    list_filter = ("role", "scope")


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ("name", "code")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "province")
    list_filter = ("province",)


@admin.register(Axis)
class AxisAdmin(admin.ModelAdmin):
    list_display = ("name", "city")
    list_filter = ("city",)


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "infrastructure_type", "is_active", "public_visible")
    list_filter = ("infrastructure_type", "is_active", "public_visible")


@admin.register(InfrastructureFeature)
class InfrastructureFeatureAdmin(admin.ModelAdmin):
    list_display = ("name", "layer", "province", "city", "sensitivity_level", "status", "updated_at")
    list_filter = ("layer", "sensitivity_level", "status")
    search_fields = ("name", "manager_name")


@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "layer", "action", "status", "submitted_by", "reviewed_by", "updated_at")
    list_filter = ("action", "status", "layer")
    search_fields = ("comment", "review_comment")


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ("title", "publish_date", "is_published")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("subject", "category", "status", "email", "created_at")
    list_filter = ("category", "status")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "actor", "action", "target_type", "target_id", "ip_address")
    list_filter = ("action", "target_type")
    search_fields = ("actor__username", "action", "target_type", "target_id")
