from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ChangeRequest, InfrastructureFeature, Layer, Province, UserProfile


class PortalViewsTest(TestCase):
    def setUp(self):
        self.layer_public = Layer.objects.create(
            key="electricite",
            name="Electricite",
            infrastructure_type=Layer.InfrastructureType.ELECTRICITY,
            public_visible=True,
        )
        self.layer_private = Layer.objects.create(
            key="fibre-telecom",
            name="Fibre",
            infrastructure_type=Layer.InfrastructureType.FIBER_TELECOM,
            public_visible=False,
        )
        province = Province.objects.create(name="Kinshasa", code="KIN")
        InfrastructureFeature.objects.create(
            name="Poste A",
            layer=self.layer_public,
            province=province,
            geometry={"type": "Point", "coordinates": [15.0, -4.0]},
            properties={"name": "Poste A"},
        )
        InfrastructureFeature.objects.create(
            name="Noeud prive",
            layer=self.layer_private,
            province=province,
            geometry={"type": "Point", "coordinates": [15.2, -4.2]},
            properties={"name": "Noeud prive"},
            sensitivity_level=InfrastructureFeature.Sensitivity.RESTRICTED,
        )

    def test_public_map_api_hides_restricted_features(self):
        response = self.client.get(reverse("portal:map_features_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["features"]), 1)

    def test_institution_editor_can_submit_change_request(self):
        user = User.objects.create_user(username="editor", password="StrongPwd123!")
        profile = user.profile
        profile.role = UserProfile.Role.INSTITUTION_EDITOR
        profile.save()

        self.client.login(username="editor", password="StrongPwd123!")

        response = self.client.post(
            reverse("portal:institution_data_new"),
            {
                "layer": self.layer_public.id,
                "action": ChangeRequest.Action.CREATE,
                "comment": "Creation d'un nouveau poste dans la zone pilote.",
                "proposed_properties": '{"name": "Nouveau poste"}',
                "proposed_geometry": '{"type": "Point", "coordinates": [15.12, -4.18]}',
                "work_type": "Pose de cable",
                "excavation_depth": "1.2m",
                "excavation_start_date": "2026-03-10",
                "excavation_end_date": "2026-04-02",
                "entity_name": "Entreprise ABC",
                "contact_details": "contact@abc.cd / +243 000 111 222",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ChangeRequest.objects.count(), 1)
        self.assertEqual(ChangeRequest.objects.first().status, ChangeRequest.Status.SUBMITTED)
