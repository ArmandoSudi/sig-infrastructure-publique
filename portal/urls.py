from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("map", views.map_page, name="map"),
    path("api/map/features", views.map_features_api, name="map_features_api"),
    path("actualites", views.news_list, name="news_list"),
    path("actualites/<slug:slug>", views.news_detail, name="news_detail"),
    path("infrastructures/<slug:layer_key>", views.infrastructure_page, name="infrastructure_page"),
    path("zones/provinces", views.zone_provinces, name="zone_provinces"),
    path("zones/provinces/<int:pk>", views.zone_province_detail, name="zone_province_detail"),
    path("zones/villes", views.zone_cities, name="zone_cities"),
    path("zones/villes/<int:pk>", views.zone_city_detail, name="zone_city_detail"),
    path("zones/axes", views.zone_axes, name="zone_axes"),
    path("zones/axes/<int:pk>", views.zone_axis_detail, name="zone_axis_detail"),
    path("documentation", views.documentation, name="documentation"),
    path("documentation/<slug:slug>", views.documentation_page, name="documentation_page"),
    path("contact", views.contact, name="contact"),
    path("support", views.support, name="support"),
    path("signalement", views.report_issue, name="report"),
    path("auth/login", views.PortalLoginView.as_view(), name="login"),
    path("auth/logout", views.portal_logout, name="logout"),
    path("institution/dashboard", views.institution_dashboard, name="institution_dashboard"),
    path("institution/data", views.institution_data, name="institution_data"),
    path("institution/data/new", views.institution_data_new, name="institution_data_new"),
    path("institution/data/<int:feature_id>/edit", views.institution_data_edit, name="institution_data_edit"),
    path("institution/history", views.institution_history, name="institution_history"),
    path("institution/history/<int:request_id>", views.institution_request_detail, name="institution_request_detail"),
    path("admin/users", views.admin_users, name="admin_users"),
    path("admin/validation", views.admin_validation, name="admin_validation"),
    path("admin/layers", views.admin_layers, name="admin_layers"),
    path("admin/audit", views.admin_audit, name="admin_audit"),
]
