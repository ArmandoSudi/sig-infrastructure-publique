import json

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChangeRequestForm, SupportTicketForm
from .models import (
    AuditLog,
    Axis,
    ChangeRequest,
    City,
    InfrastructureFeature,
    Layer,
    NewsPost,
    Province,
    UserProfile,
)
from .utils import get_user_role, log_action, role_required


LAYER_PAGE_BY_KEY = {
    "electricite": "ELECTRICITY",
    "eau-assainissement": "WATER_SANITATION",
    "fibre-telecom": "FIBER_TELECOM",
    "voirie": "ROADS",
    "caniveaux-drainage": "DRAINAGE",
}


class PortalLoginView(LoginView):
    template_name = "portal/auth/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        role = get_user_role(self.request.user)
        if role in {UserProfile.Role.NATIONAL_ADMIN, UserProfile.Role.PROVINCIAL_ADMIN}:
            return "/admin/validation"
        if role in {UserProfile.Role.INSTITUTION_READER, UserProfile.Role.INSTITUTION_EDITOR}:
            return "/institution/dashboard"
        return "/"


@login_required
@require_POST
def portal_logout(request):
    logout(request)
    messages.success(request, "Vous avez ete deconnecte.")
    return redirect("portal:home")


def _visible_layers_for_user(user):
    layers = Layer.objects.filter(is_active=True)
    role = get_user_role(user)
    if role == UserProfile.Role.PUBLIC_READER:
        return layers.filter(public_visible=True)
    return layers


def _feature_queryset_for_user(user):
    features = InfrastructureFeature.objects.select_related("layer", "province", "city", "axis")
    role = get_user_role(user)

    if role == UserProfile.Role.PUBLIC_READER:
        return features.filter(layer__public_visible=True, sensitivity_level=InfrastructureFeature.Sensitivity.PUBLIC)

    profile = getattr(user, "profile", None)
    if not profile or profile.scope == UserProfile.Scope.NATIONAL:
        return features

    if profile.scope == UserProfile.Scope.PROVINCE and profile.scope_value:
        return features.filter(Q(province__name__iexact=profile.scope_value) | Q(province__code__iexact=profile.scope_value))

    if profile.scope == UserProfile.Scope.CITY and profile.scope_value:
        return features.filter(city__name__iexact=profile.scope_value)

    return features


def home(request):
    layers = _visible_layers_for_user(request.user)
    stats = _feature_queryset_for_user(request.user).values("layer__name").annotate(total=Count("id"))
    recent_news = NewsPost.objects.filter(is_published=True)[:5]
    recent_updates = ChangeRequest.objects.select_related("layer", "submitted_by").filter(status=ChangeRequest.Status.SUBMITTED)[:5]
    context = {
        "layers": layers,
        "stats": stats,
        "recent_news": recent_news,
        "recent_updates": recent_updates,
    }
    return render(request, "portal/home.html", context)


def map_page(request):
    context = {
        "layers": _visible_layers_for_user(request.user),
        "active_layer": request.GET.get("layer", ""),
        "title": "Carte nationale",
        "subtitle": "Visualisez les couches d'infrastructures et filtrez par zone.",
    }
    return render(request, "portal/map.html", context)


def infrastructure_page(request, layer_key):
    layer_type = LAYER_PAGE_BY_KEY.get(layer_key)
    if not layer_type:
        return redirect("portal:map")

    layer = get_object_or_404(Layer, infrastructure_type=layer_type, is_active=True)
    visible_layers = _visible_layers_for_user(request.user)
    can_view_layer_data = visible_layers.filter(pk=layer.pk).exists()
    context = {
        "layers": visible_layers,
        "active_layer": layer.key if can_view_layer_data else "",
        "title": layer.name,
        "subtitle": layer.description or f"Carte thematique pour {layer.name.lower()}.",
        "layer": layer,
        "visibility_note": "" if can_view_layer_data else "Cette couche est reservee aux comptes institutionnels autorises.",
    }
    return render(request, "portal/map.html", context)


def map_features_api(request):
    features = _feature_queryset_for_user(request.user)

    layer = request.GET.get("layer")
    province = request.GET.get("province")
    city = request.GET.get("city")
    axis = request.GET.get("axis")
    search = request.GET.get("q")

    if layer:
        features = features.filter(layer__key=layer)
    if province:
        features = features.filter(province__name__icontains=province)
    if city:
        features = features.filter(city__name__icontains=city)
    if axis:
        features = features.filter(axis__name__icontains=axis)
    if search:
        features = features.filter(
            Q(name__icontains=search) | Q(manager_name__icontains=search)
        )

    include_sensitive = request.user.is_authenticated and get_user_role(request.user) != UserProfile.Role.PUBLIC_READER
    payload = {
        "type": "FeatureCollection",
        "features": [feature.to_geojson_feature(include_sensitive=include_sensitive) for feature in features[:500]],
    }
    return JsonResponse(payload)


def news_list(request):
    posts = NewsPost.objects.filter(is_published=True)
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "portal/news_list.html", {"page_obj": page_obj})


def news_detail(request, slug):
    post = get_object_or_404(NewsPost, slug=slug, is_published=True)
    return render(request, "portal/news_detail.html", {"post": post})


def zone_provinces(request):
    provinces = Province.objects.annotate(feature_count=Count("features"))
    return render(request, "portal/zone_list.html", {"title": "Provinces", "items": provinces, "item_type": "province"})


def zone_province_detail(request, pk):
    province = get_object_or_404(Province, pk=pk)
    features = _feature_queryset_for_user(request.user).filter(province=province)[:100]
    return render(
        request,
        "portal/zone_detail.html",
        {"title": province.name, "subtitle": "Infrastructures de la province", "features": features},
    )


def zone_cities(request):
    cities = City.objects.select_related("province").annotate(feature_count=Count("features"))
    return render(request, "portal/zone_list.html", {"title": "Villes et communes", "items": cities, "item_type": "city"})


def zone_city_detail(request, pk):
    city = get_object_or_404(City, pk=pk)
    features = _feature_queryset_for_user(request.user).filter(city=city)[:100]
    return render(request, "portal/zone_detail.html", {"title": city.name, "subtitle": city.province.name, "features": features})


def zone_axes(request):
    axes = Axis.objects.select_related("city", "city__province").annotate(feature_count=Count("features"))
    return render(request, "portal/zone_list.html", {"title": "Axes et quartiers", "items": axes, "item_type": "axis"})


def zone_axis_detail(request, pk):
    axis = get_object_or_404(Axis, pk=pk)
    features = _feature_queryset_for_user(request.user).filter(axis=axis)[:100]
    subtitle = f"{axis.city.name} - {axis.city.province.name}"
    return render(request, "portal/zone_detail.html", {"title": axis.name, "subtitle": subtitle, "features": features})


def documentation(request):
    sections = [
        ("Guide d'utilisation", "guide"),
        ("Normes de saisie", "normes"),
        ("References techniques", "references"),
    ]
    return render(request, "portal/docs.html", {"title": "Documentation", "sections": sections, "active": "overview"})


def documentation_page(request, slug):
    titles = {
        "guide": "Guide d'utilisation",
        "normes": "Normes de saisie des donnees",
        "references": "References techniques et legales",
    }
    if slug not in titles:
        return redirect("portal:documentation")
    return render(
        request,
        "portal/docs.html",
        {
            "title": titles[slug],
            "active": slug,
            "sections": [(label, key) for key, label in titles.items()],
        },
    )


def contact(request):
    return render(request, "portal/contact.html")


def support(request):
    form = SupportTicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ticket = form.save(commit=False)
        ticket.category = ticket.Category.SUPPORT
        ticket.save()
        log_action(request, "SUPPORT_TICKET_CREATED", "SupportTicket", ticket.pk, {"category": ticket.category})
        messages.success(request, "Votre demande de support a ete enregistree.")
        return redirect("portal:support")
    return render(request, "portal/support.html", {"form": form})


def report_issue(request):
    form = SupportTicketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ticket = form.save(commit=False)
        ticket.category = ticket.Category.ANOMALY
        ticket.save()
        log_action(request, "ANOMALY_REPORTED", "SupportTicket", ticket.pk, {"category": ticket.category})
        messages.success(request, "Merci. Le signalement a ete transmis a l'equipe technique.")
        return redirect("portal:report")
    return render(request, "portal/report.html", {"form": form})


@role_required(
    UserProfile.Role.INSTITUTION_READER,
    UserProfile.Role.INSTITUTION_EDITOR,
    UserProfile.Role.PROVINCIAL_ADMIN,
    UserProfile.Role.NATIONAL_ADMIN,
)
def institution_dashboard(request):
    owned_requests = ChangeRequest.objects.filter(submitted_by=request.user)
    context = {
        "submitted": owned_requests.count(),
        "pending": owned_requests.filter(status=ChangeRequest.Status.SUBMITTED).count(),
        "approved": owned_requests.filter(status=ChangeRequest.Status.APPROVED).count(),
        "rejected": owned_requests.filter(status=ChangeRequest.Status.REJECTED).count(),
        "recent": owned_requests.select_related("layer")[:8],
    }
    log_action(request, "INSTITUTION_DASHBOARD_VIEW", "Dashboard")
    return render(request, "portal/institution/dashboard.html", context)


@role_required(
    UserProfile.Role.INSTITUTION_READER,
    UserProfile.Role.INSTITUTION_EDITOR,
    UserProfile.Role.PROVINCIAL_ADMIN,
    UserProfile.Role.NATIONAL_ADMIN,
)
def institution_data(request):
    data = _feature_queryset_for_user(request.user).order_by("-updated_at")
    return render(request, "portal/institution/data_list.html", {"features": data[:200]})


@role_required(
    UserProfile.Role.INSTITUTION_EDITOR,
    UserProfile.Role.PROVINCIAL_ADMIN,
    UserProfile.Role.NATIONAL_ADMIN,
)
def institution_data_new(request):
    initial = {
        "action": ChangeRequest.Action.CREATE,
        "proposed_properties": json.dumps({"name": "", "manager_name": ""}, indent=2),
        "proposed_geometry": json.dumps({"type": "Point", "coordinates": [15.26, -4.32]}, indent=2),
    }
    form = ChangeRequestForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        req = form.save(commit=False)
        req.status = ChangeRequest.Status.SUBMITTED
        req.submitted_by = request.user
        req.submitted_at = timezone.now()
        req.save()
        log_action(request, "CHANGE_REQUEST_SUBMITTED", "ChangeRequest", req.pk, {"action": req.action})
        messages.success(request, "La soumission a ete envoyee pour validation.")
        return redirect("portal:institution_history")
    return render(request, "portal/institution/change_form.html", {"title": "Nouvelle soumission", "form": form})


@role_required(
    UserProfile.Role.INSTITUTION_EDITOR,
    UserProfile.Role.PROVINCIAL_ADMIN,
    UserProfile.Role.NATIONAL_ADMIN,
)
def institution_data_edit(request, feature_id):
    feature = get_object_or_404(_feature_queryset_for_user(request.user), pk=feature_id)
    initial = {
        "layer": feature.layer,
        "action": ChangeRequest.Action.UPDATE,
        "proposed_properties": json.dumps(feature.properties, indent=2),
        "proposed_geometry": json.dumps(feature.geometry, indent=2),
    }
    form = ChangeRequestForm(request.POST or None, request.FILES or None, initial=initial)
    form.fields["layer"].disabled = True
    form.fields["action"].disabled = True

    if request.method == "POST" and form.is_valid():
        req = form.save(commit=False)
        req.feature = feature
        req.layer = feature.layer
        req.action = ChangeRequest.Action.UPDATE
        req.status = ChangeRequest.Status.SUBMITTED
        req.submitted_by = request.user
        req.submitted_at = timezone.now()
        req.save()
        log_action(request, "CHANGE_REQUEST_SUBMITTED", "ChangeRequest", req.pk, {"action": req.action, "feature": feature.pk})
        messages.success(request, "Modification soumise. En attente de validation.")
        return redirect("portal:institution_history")

    return render(
        request,
        "portal/institution/change_form.html",
        {"title": f"Modifier {feature.name}", "form": form, "feature": feature},
    )


@role_required(
    UserProfile.Role.INSTITUTION_READER,
    UserProfile.Role.INSTITUTION_EDITOR,
    UserProfile.Role.PROVINCIAL_ADMIN,
    UserProfile.Role.NATIONAL_ADMIN,
)
def institution_history(request):
    history = ChangeRequest.objects.select_related("layer", "submitted_by", "reviewed_by")
    role = get_user_role(request.user)
    if role in {UserProfile.Role.INSTITUTION_READER, UserProfile.Role.INSTITUTION_EDITOR}:
        history = history.filter(submitted_by=request.user)

    status = request.GET.get("status")
    layer = request.GET.get("layer")
    if status:
        history = history.filter(status=status)
    if layer:
        history = history.filter(layer__key=layer)

    return render(
        request,
        "portal/institution/history.html",
        {
            "history": history[:200],
            "layers": Layer.objects.filter(is_active=True),
            "status": status,
            "selected_layer": layer,
            "status_choices": ChangeRequest.Status.choices,
        },
    )


@role_required(
    UserProfile.Role.INSTITUTION_READER,
    UserProfile.Role.INSTITUTION_EDITOR,
    UserProfile.Role.PROVINCIAL_ADMIN,
    UserProfile.Role.NATIONAL_ADMIN,
)
def institution_request_detail(request, request_id):
    queryset = ChangeRequest.objects.select_related("layer", "feature", "submitted_by", "reviewed_by")
    role = get_user_role(request.user)
    if role in {UserProfile.Role.INSTITUTION_READER, UserProfile.Role.INSTITUTION_EDITOR}:
        queryset = queryset.filter(submitted_by=request.user)

    change_request = get_object_or_404(queryset, pk=request_id)
    can_edit = (
        change_request.submitted_by == request.user
        and role in {UserProfile.Role.INSTITUTION_EDITOR, UserProfile.Role.PROVINCIAL_ADMIN, UserProfile.Role.NATIONAL_ADMIN}
        and change_request.status in {ChangeRequest.Status.NEEDS_CHANGES, ChangeRequest.Status.REJECTED, ChangeRequest.Status.DRAFT}
    )

    form = None
    if can_edit:
        form = ChangeRequestForm(request.POST or None, request.FILES or None, instance=change_request)
        form.fields["layer"].disabled = True
        form.fields["action"].disabled = True
        if request.method == "POST" and form.is_valid():
            updated = form.save(commit=False)
            updated.status = ChangeRequest.Status.SUBMITTED
            updated.submitted_at = timezone.now()
            updated.save()
            log_action(
                request,
                "CHANGE_REQUEST_RESUBMITTED",
                "ChangeRequest",
                updated.pk,
                {"action": updated.action},
            )
            messages.success(request, "Soumission mise a jour et renvoyee pour validation.")
            return redirect("portal:institution_history")

    return render(
        request,
        "portal/institution/request_detail.html",
        {
            "item": change_request,
            "can_edit": can_edit,
            "form": form,
        },
    )


@role_required(UserProfile.Role.PROVINCIAL_ADMIN, UserProfile.Role.NATIONAL_ADMIN)
def admin_users(request):
    profiles = UserProfile.objects.select_related("user", "institution").order_by("user__username")
    if request.method == "POST":
        profile = get_object_or_404(UserProfile, pk=request.POST.get("profile_id"))
        profile.role = request.POST.get("role", profile.role)
        profile.scope = request.POST.get("scope", profile.scope)
        profile.scope_value = request.POST.get("scope_value", profile.scope_value)
        profile.save(update_fields=["role", "scope", "scope_value", "updated_at"])
        profile.user.is_active = bool(request.POST.get("is_active"))
        profile.user.save(update_fields=["is_active"])
        log_action(request, "USER_PROFILE_UPDATED", "UserProfile", profile.pk, {"role": profile.role, "scope": profile.scope})
        messages.success(request, f"Profil de {profile.user.username} mis a jour.")
        return redirect("portal:admin_users")

    return render(
        request,
        "portal/admin/users.html",
        {"profiles": profiles, "roles": UserProfile.Role.choices, "scopes": UserProfile.Scope.choices},
    )


@role_required(UserProfile.Role.PROVINCIAL_ADMIN, UserProfile.Role.NATIONAL_ADMIN)
def admin_validation(request):
    queue = list(
        ChangeRequest.objects.select_related("submitted_by", "layer", "feature").filter(
            status=ChangeRequest.Status.SUBMITTED
        )
    )
    for item in queue:
        item.proposed_geometry_json = json.dumps(item.proposed_geometry or {})
        item.current_geometry_json = json.dumps(item.feature.geometry if item.feature else {})
        item.proposed_script_id = f"proposed-geometry-{item.id}"
        item.current_script_id = f"current-geometry-{item.id}"

    if request.method == "POST":
        req = get_object_or_404(ChangeRequest, pk=request.POST.get("request_id"))
        decision = request.POST.get("decision")
        comment = request.POST.get("review_comment", "")
        try:
            if decision == "approve":
                req.approve(request.user, comment)
                messages.success(request, f"Soumission #{req.pk} approuvee.")
                log_action(request, "CHANGE_REQUEST_APPROVED", "ChangeRequest", req.pk)
            elif decision == "reject":
                req.reject(request.user, comment)
                messages.warning(request, f"Soumission #{req.pk} rejetee.")
                log_action(request, "CHANGE_REQUEST_REJECTED", "ChangeRequest", req.pk)
            elif decision == "needs_changes":
                req.status = ChangeRequest.Status.NEEDS_CHANGES
                req.reviewed_by = request.user
                req.reviewed_at = timezone.now()
                req.review_comment = comment
                req.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_comment", "updated_at"])
                messages.info(request, f"Soumission #{req.pk} retournee pour correction.")
                log_action(request, "CHANGE_REQUEST_NEEDS_CHANGES", "ChangeRequest", req.pk)
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("portal:admin_validation")

    return render(request, "portal/admin/validation.html", {"queue": queue[:200]})


@role_required(UserProfile.Role.PROVINCIAL_ADMIN, UserProfile.Role.NATIONAL_ADMIN)
def admin_layers(request):
    layers = Layer.objects.order_by("name")
    if request.method == "POST":
        layer = get_object_or_404(Layer, pk=request.POST.get("layer_id"))
        layer.is_active = bool(request.POST.get("is_active"))
        layer.public_visible = bool(request.POST.get("public_visible"))
        layer.sensitive_fields = [
            field.strip() for field in request.POST.get("sensitive_fields", "").split(",") if field.strip()
        ]
        layer.visible_fields = [field.strip() for field in request.POST.get("visible_fields", "").split(",") if field.strip()]
        layer.save(update_fields=["is_active", "public_visible", "sensitive_fields", "visible_fields", "updated_at"])
        log_action(request, "LAYER_CONFIG_UPDATED", "Layer", layer.pk)
        messages.success(request, f"Configuration de la couche {layer.name} enregistree.")
        return redirect("portal:admin_layers")
    return render(request, "portal/admin/layers.html", {"layers": layers})


@role_required(UserProfile.Role.PROVINCIAL_ADMIN, UserProfile.Role.NATIONAL_ADMIN)
def admin_audit(request):
    logs = AuditLog.objects.select_related("actor")
    action = request.GET.get("action")
    actor = request.GET.get("actor")
    if action:
        logs = logs.filter(action__icontains=action)
    if actor:
        logs = logs.filter(actor__username__icontains=actor)

    return render(request, "portal/admin/audit.html", {"logs": logs[:300], "action": action, "actor": actor})
