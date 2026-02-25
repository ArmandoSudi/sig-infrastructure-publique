import json

from django import forms
from django.contrib.auth.models import User

from .models import ChangeRequest, Layer, SupportTicket, UserProfile


class JsonTextareaField(forms.CharField):
    def to_python(self, value):
        value = super().to_python(value)
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"JSON invalide: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("Le contenu JSON doit etre un objet.")
        return parsed


class ChangeRequestForm(forms.ModelForm):
    kml_file = forms.FileField(
        required=False,
        help_text="Importer un fichier KML si vous n'avez pas de GeoJSON.",
    )
    proposed_properties = JsonTextareaField(
        widget=forms.Textarea(attrs={"rows": 8, "class": "code-textarea"}),
        required=False,
        help_text="Objet JSON: attributs modifies ou nouveaux.",
    )
    proposed_geometry = JsonTextareaField(
        widget=forms.Textarea(attrs={"rows": 8, "class": "code-textarea"}),
        required=False,
        help_text='Objet GeoJSON (Feature ou FeatureCollection) ou geometrie (ex. {"type":"Point","coordinates":[15.3,-4.3]}).',
    )

    class Meta:
        model = ChangeRequest
        fields = [
            "layer",
            "action",
            "kml_file",
            "proposed_geometry",
            "proposed_properties",
            "work_type",
            "excavation_depth",
            "excavation_start_date",
            "excavation_end_date",
            "entity_name",
            "contact_details",
            "comment",
        ]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3}),
            "contact_details": forms.Textarea(attrs={"rows": 3}),
            "excavation_start_date": forms.DateInput(attrs={"type": "date"}),
            "excavation_end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["layer"].queryset = Layer.objects.filter(is_active=True).order_by("name")
        self.fields["work_type"].required = True
        self.fields["excavation_depth"].required = True
        self.fields["excavation_start_date"].required = True
        self.fields["excavation_end_date"].required = True
        self.fields["entity_name"].required = True
        self.fields["contact_details"].required = True
        if not self.is_bound and self.instance and self.instance.pk:
            self.initial.setdefault("proposed_properties", json.dumps(self.instance.proposed_properties, indent=2))
            self.initial.setdefault("proposed_geometry", json.dumps(self.instance.proposed_geometry, indent=2))

    def clean(self):
        cleaned_data = super().clean()
        kml_file = cleaned_data.get("kml_file")
        geometry = cleaned_data.get("proposed_geometry")
        start_date = cleaned_data.get("excavation_start_date")
        end_date = cleaned_data.get("excavation_end_date")
        if not kml_file and not geometry:
            raise forms.ValidationError("Veuillez fournir un fichier KML ou des donnees GeoJSON.")
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("La date de fin doit etre posterieure a la date de debut.")
        return cleaned_data

    def clean_comment(self):
        value = self.cleaned_data["comment"].strip()
        if len(value) < 10:
            raise forms.ValidationError("Ajoutez un commentaire plus detaille (10 caracteres min).")
        return value


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["full_name", "email", "subject", "related_zone", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["role", "scope", "scope_value", "institution"]


class UserActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["is_active"]
