from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from portal.models import (
    Axis,
    City,
    InfrastructureFeature,
    Institution,
    Layer,
    NewsPost,
    Province,
    UserProfile,
)


class Command(BaseCommand):
    help = "Seed demo data for the SIG infrastructure portal"

    def handle(self, *args, **options):
        institution, _ = Institution.objects.get_or_create(
            name="ARPTC",
            defaults={
                "institution_type": Institution.InstitutionType.MINISTRY,
                "contact_email": "contact@arptc.cd",
            },
        )

        layers_config = [
            {
                "name": "Electricite",
                "key": "electricite",
                "infrastructure_type": Layer.InfrastructureType.ELECTRICITY,
                "description": "Lignes, postes et cables souterrains.",
                "style_config": {"color": "#f97316"},
                "sensitive_fields": ["voltage", "critical_node"],
                "visible_fields": ["name", "status", "manager_name", "updated_at"],
            },
            {
                "name": "Eau & Assainissement",
                "key": "eau-assainissement",
                "infrastructure_type": Layer.InfrastructureType.WATER_SANITATION,
                "description": "Reseaux, stations et egouts.",
                "style_config": {"color": "#3b82f6"},
                "sensitive_fields": ["pressure_psi"],
                "visible_fields": ["name", "status", "manager_name", "updated_at"],
            },
            {
                "name": "Fibre & Telecom",
                "key": "fibre-telecom",
                "infrastructure_type": Layer.InfrastructureType.FIBER_TELECOM,
                "description": "Fibre optique, antennes et centres telecom.",
                "style_config": {"color": "#0ea5a4"},
                "public_visible": False,
                "sensitive_fields": ["core_route"],
                "visible_fields": ["name", "status", "manager_name", "updated_at"],
            },
            {
                "name": "Voirie",
                "key": "voirie",
                "infrastructure_type": Layer.InfrastructureType.ROADS,
                "description": "Routes, ponts et tunnels.",
                "style_config": {"color": "#64748b"},
                "visible_fields": ["name", "status", "manager_name", "updated_at"],
            },
            {
                "name": "Caniveaux & Drainage",
                "key": "caniveaux-drainage",
                "infrastructure_type": Layer.InfrastructureType.DRAINAGE,
                "description": "Canaux, drains et zones a risque.",
                "style_config": {"color": "#16a34a"},
                "visible_fields": ["name", "status", "manager_name", "updated_at"],
            },
        ]

        layers = {}
        for config in layers_config:
            layer, _ = Layer.objects.update_or_create(key=config["key"], defaults=config)
            layers[layer.key] = layer

        kin, _ = Province.objects.get_or_create(name="Kinshasa", code="KIN")
        kat, _ = Province.objects.get_or_create(name="Haut-Katanga", code="HKA")

        gombe, _ = City.objects.get_or_create(province=kin, name="Gombe")
        limete, _ = City.objects.get_or_create(province=kin, name="Limete")
        lubumbashi, _ = City.objects.get_or_create(province=kat, name="Lubumbashi")

        boulevard, _ = Axis.objects.get_or_create(city=gombe, name="Boulevard du 30 Juin")
        arret_bus, _ = Axis.objects.get_or_create(city=limete, name="Axe Industriel")
        kasapa, _ = Axis.objects.get_or_create(city=lubumbashi, name="Kasapa Corridor")

        demo_features = [
            {
                "name": "Poste haute tension Gombe",
                "layer": layers["electricite"],
                "province": kin,
                "city": gombe,
                "axis": boulevard,
                "geometry": {"type": "Point", "coordinates": [15.3034, -4.3191]},
                "properties": {
                    "name": "Poste haute tension Gombe",
                    "manager_name": "SNEL",
                    "voltage": "220kV",
                    "critical_node": True,
                },
            },
            {
                "name": "Collecteur principal Limete",
                "layer": layers["eau-assainissement"],
                "province": kin,
                "city": limete,
                "axis": arret_bus,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[15.33, -4.36], [15.35, -4.355], [15.37, -4.349]],
                },
                "geometry_type": InfrastructureFeature.GeometryType.LINE,
                "properties": {
                    "name": "Collecteur principal Limete",
                    "manager_name": "REGIDESO",
                    "pressure_psi": 72,
                },
            },
            {
                "name": "Noeud fibre Kasapa",
                "layer": layers["fibre-telecom"],
                "province": kat,
                "city": lubumbashi,
                "axis": kasapa,
                "sensitivity_level": InfrastructureFeature.Sensitivity.RESTRICTED,
                "geometry": {"type": "Point", "coordinates": [27.4892, -11.6644]},
                "properties": {
                    "name": "Noeud fibre Kasapa",
                    "manager_name": "Societe Telecom Nationale",
                    "core_route": "KSP-BACKBONE-01",
                },
            },
            {
                "name": "Pont urbain Lubumbashi",
                "layer": layers["voirie"],
                "province": kat,
                "city": lubumbashi,
                "axis": kasapa,
                "geometry": {"type": "Point", "coordinates": [27.477, -11.6702]},
                "properties": {
                    "name": "Pont urbain Lubumbashi",
                    "manager_name": "Office des routes",
                    "condition": "A surveiller",
                },
            },
            {
                "name": "Zone drainage inondable Ndjili",
                "layer": layers["caniveaux-drainage"],
                "province": kin,
                "city": limete,
                "axis": arret_bus,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[15.39, -4.38], [15.41, -4.38], [15.41, -4.36], [15.39, -4.36], [15.39, -4.38]]],
                },
                "geometry_type": InfrastructureFeature.GeometryType.POLYGON,
                "properties": {
                    "name": "Zone drainage inondable Ndjili",
                    "manager_name": "OVD",
                    "risk_level": "Eleve",
                },
            },
        ]

        for payload in demo_features:
            defaults = payload.copy()
            name = defaults.pop("name")
            defaults.setdefault("geometry_type", defaults["geometry"]["type"])
            defaults.setdefault("manager_name", defaults.get("properties", {}).get("manager_name", ""))
            InfrastructureFeature.objects.update_or_create(name=name, layer=defaults["layer"], defaults=defaults)

        posts = [
            (
                "Demarrage du pilote SIG a Kinshasa",
                "Le portail national SIG entre en phase pilote avec les premieres couches institutionnelles.",
            ),
            (
                "Atelier inter-institutionnel sur la qualite des donnees",
                "Les ministeres sectoriels harmonisent les normes de saisie GeoJSON et metadata.",
            ),
        ]

        for title, content in posts:
            NewsPost.objects.update_or_create(
                slug=slugify(title),
                defaults={
                    "title": title,
                    "summary": content,
                    "content": content,
                    "is_published": True,
                },
            )

        users_data = [
            {
                "username": "national_admin",
                "password": "Admin12345!",
                "email": "national.admin@sig.cd",
                "role": UserProfile.Role.NATIONAL_ADMIN,
                "scope": UserProfile.Scope.NATIONAL,
            },
            {
                "username": "prov_admin_kin",
                "password": "Admin12345!",
                "email": "prov.kin@sig.cd",
                "role": UserProfile.Role.PROVINCIAL_ADMIN,
                "scope": UserProfile.Scope.PROVINCE,
                "scope_value": "Kinshasa",
            },
            {
                "username": "inst_editor",
                "password": "Editor12345!",
                "email": "editor@sig.cd",
                "role": UserProfile.Role.INSTITUTION_EDITOR,
                "scope": UserProfile.Scope.NATIONAL,
            },
            {
                "username": "inst_reader",
                "password": "Reader12345!",
                "email": "reader@sig.cd",
                "role": UserProfile.Role.INSTITUTION_READER,
                "scope": UserProfile.Scope.NATIONAL,
            },
        ]

        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={"email": data["email"], "is_staff": False},
            )
            if created:
                user.set_password(data["password"])
                user.save(update_fields=["password"])
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = data["role"]
            profile.scope = data["scope"]
            profile.scope_value = data.get("scope_value", "")
            profile.institution = institution
            profile.save()

        self.stdout.write(self.style.SUCCESS("Demo SIG data seeded successfully."))
