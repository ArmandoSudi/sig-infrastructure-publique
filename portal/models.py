import uuid

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Institution(TimeStampedModel):
    class InstitutionType(models.TextChoices):
        MINISTRY = "MINISTRY", "Ministere"
        PUBLIC_SERVICE = "PUBLIC_SERVICE", "Service public"
        CITY = "CITY", "Collectivite"
        OPERATOR = "OPERATOR", "Operateur"
        OTHER = "OTHER", "Autre"

    name = models.CharField(max_length=180, unique=True)
    institution_type = models.CharField(max_length=30, choices=InstitutionType.choices, default=InstitutionType.OTHER)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserProfile(TimeStampedModel):
    class Role(models.TextChoices):
        PUBLIC_READER = "PUBLIC_READER", "Public Reader"
        INSTITUTION_READER = "INSTITUTION_READER", "Institution Reader"
        INSTITUTION_EDITOR = "INSTITUTION_EDITOR", "Institution Editor"
        PROVINCIAL_ADMIN = "PROVINCIAL_ADMIN", "Provincial Admin"
        NATIONAL_ADMIN = "NATIONAL_ADMIN", "National Admin"

    class Scope(models.TextChoices):
        NATIONAL = "NATIONAL", "National"
        PROVINCE = "PROVINCE", "Province"
        CITY = "CITY", "Ville"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    institution = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.SET_NULL)
    role = models.CharField(max_length=25, choices=Role.choices, default=Role.PUBLIC_READER)
    scope = models.CharField(max_length=10, choices=Scope.choices, default=Scope.NATIONAL)
    scope_value = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Province(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=8, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class City(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]
        unique_together = [("province", "name")]

    def __str__(self):
        return f"{self.name}, {self.province.code}"


class Axis(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="axes")
    name = models.CharField(max_length=160)

    class Meta:
        ordering = ["name"]
        unique_together = [("city", "name")]

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class Layer(TimeStampedModel):
    class InfrastructureType(models.TextChoices):
        ELECTRICITY = "ELECTRICITY", "Electricite"
        WATER_SANITATION = "WATER_SANITATION", "Eau et assainissement"
        FIBER_TELECOM = "FIBER_TELECOM", "Fibre et telecom"
        ROADS = "ROADS", "Voirie"
        DRAINAGE = "DRAINAGE", "Caniveaux et drainage"

    key = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=180)
    infrastructure_type = models.CharField(max_length=20, choices=InfrastructureType.choices)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    public_visible = models.BooleanField(default=True)
    style_config = models.JSONField(default=dict, blank=True)
    visible_fields = models.JSONField(default=list, blank=True)
    required_fields = models.JSONField(default=list, blank=True)
    sensitive_fields = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class InfrastructureFeature(TimeStampedModel):
    class GeometryType(models.TextChoices):
        POINT = "Point", "Point"
        LINE = "LineString", "Line"
        POLYGON = "Polygon", "Polygon"

    class Sensitivity(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        RESTRICTED = "RESTRICTED", "Restreint"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        PLANNED = "PLANNED", "Planifie"
        MAINTENANCE = "MAINTENANCE", "Maintenance"

    feature_uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=180)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name="features")
    manager_name = models.CharField(max_length=180, blank=True)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, related_name="features")
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name="features")
    axis = models.ForeignKey(Axis, on_delete=models.SET_NULL, null=True, blank=True, related_name="features")
    geometry_type = models.CharField(max_length=12, choices=GeometryType.choices, default=GeometryType.POINT)
    geometry = models.JSONField(default=dict)
    properties = models.JSONField(default=dict, blank=True)
    sensitivity_level = models.CharField(max_length=12, choices=Sensitivity.choices, default=Sensitivity.PUBLIC)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def to_geojson_feature(self, include_sensitive=False):
        properties = {
            "name": self.name,
            "manager_name": self.manager_name,
            "status": self.status,
            "layer": self.layer.name,
            "layer_key": self.layer.key,
            "city": self.city.name if self.city else "",
            "province": self.province.name if self.province else "",
            "updated_at": self.updated_at.strftime("%Y-%m-%d"),
        }
        properties.update(self.properties or {})

        if not include_sensitive:
            for field_name in self.layer.sensitive_fields:
                properties.pop(field_name, None)

        return {
            "type": "Feature",
            "id": str(self.feature_uid),
            "geometry": self.geometry,
            "properties": properties,
        }


class ChangeRequest(TimeStampedModel):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Creation"
        UPDATE = "UPDATE", "Mise a jour"
        DELETE = "DELETE", "Suppression"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        SUBMITTED = "SUBMITTED", "Soumis"
        APPROVED = "APPROVED", "Approuve"
        REJECTED = "REJECTED", "Rejete"
        NEEDS_CHANGES = "NEEDS_CHANGES", "Correction demandee"

    feature = models.ForeignKey(InfrastructureFeature, null=True, blank=True, on_delete=models.SET_NULL, related_name="change_requests")
    layer = models.ForeignKey(Layer, on_delete=models.PROTECT, related_name="change_requests")
    action = models.CharField(max_length=10, choices=Action.choices, default=Action.UPDATE)
    kml_file = models.FileField(upload_to="requests/kml/", null=True, blank=True)
    proposed_geometry = models.JSONField(default=dict, blank=True)
    proposed_properties = models.JSONField(default=dict, blank=True)
    work_type = models.CharField(max_length=180, default="")
    excavation_depth = models.CharField(max_length=50, default="")
    excavation_start_date = models.DateField(null=True, blank=True)
    excavation_end_date = models.DateField(null=True, blank=True)
    entity_name = models.CharField(max_length=180, default="")
    contact_details = models.TextField(default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    comment = models.TextField()
    review_comment = models.TextField(blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submitted_requests")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_requests")
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.get_action_display()} - {self.layer.name} ({self.status})"

    @transaction.atomic
    def approve(self, reviewer, review_comment=""):
        if self.status != self.Status.SUBMITTED:
            raise ValueError("Only submitted requests can be approved.")

        if self.action == self.Action.CREATE:
            feature_name = self.proposed_properties.get("name") or f"Nouvel objet {self.layer.name}"
            new_feature = InfrastructureFeature.objects.create(
                name=feature_name,
                layer=self.layer,
                geometry_type=(self.proposed_geometry or {}).get("type", InfrastructureFeature.GeometryType.POINT),
                geometry=self.proposed_geometry,
                properties=self.proposed_properties,
                sensitivity_level=self.proposed_properties.get("sensitivity_level", InfrastructureFeature.Sensitivity.PUBLIC),
                status=self.proposed_properties.get("status", InfrastructureFeature.Status.ACTIVE),
                manager_name=self.proposed_properties.get("manager_name", ""),
                created_by=self.submitted_by,
            )
            self.feature = new_feature
        elif self.action == self.Action.UPDATE and self.feature:
            geometry = self.proposed_geometry or self.feature.geometry
            self.feature.geometry = geometry
            self.feature.geometry_type = geometry.get("type", self.feature.geometry_type)
            merged_properties = {**self.feature.properties, **(self.proposed_properties or {})}
            self.feature.properties = merged_properties
            self.feature.name = merged_properties.get("name", self.feature.name)
            self.feature.manager_name = merged_properties.get("manager_name", self.feature.manager_name)
            self.feature.save()
        elif self.action == self.Action.DELETE and self.feature:
            self.feature.status = InfrastructureFeature.Status.MAINTENANCE
            self.feature.save(update_fields=["status", "updated_at"])

        self.status = self.Status.APPROVED
        self.review_comment = review_comment
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=[
            "feature",
            "status",
            "review_comment",
            "reviewed_by",
            "reviewed_at",
            "updated_at",
        ])

    def reject(self, reviewer, review_comment=""):
        if self.status != self.Status.SUBMITTED:
            raise ValueError("Only submitted requests can be rejected.")
        self.status = self.Status.REJECTED
        self.review_comment = review_comment
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "review_comment", "reviewed_by", "reviewed_at", "updated_at"])


class NewsPost(TimeStampedModel):
    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=230, unique=True)
    summary = models.TextField(blank=True)
    content = models.TextField()
    tags = models.CharField(max_length=220, blank=True)
    publish_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-publish_date"]

    def __str__(self):
        return self.title


class SupportTicket(TimeStampedModel):
    class Category(models.TextChoices):
        SUPPORT = "SUPPORT", "Support"
        ANOMALY = "ANOMALY", "Signalement"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Ouvert"
        IN_PROGRESS = "IN_PROGRESS", "En cours"
        CLOSED = "CLOSED", "Ferme"

    category = models.CharField(max_length=10, choices=Category.choices, default=Category.SUPPORT)
    full_name = models.CharField(max_length=140)
    email = models.EmailField()
    subject = models.CharField(max_length=180)
    message = models.TextField()
    related_zone = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.get_category_display()})"


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} - {self.target_type}"
