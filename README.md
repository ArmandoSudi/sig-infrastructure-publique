# SIG Infrastructures Publiques (Django MVP)

Plateforme web SIG pour la cartographie, la consultation et la mise a jour coordonnee des infrastructures publiques en RDC.

## Lancer le projet

```bash
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate drf
python manage.py migrate
python manage.py seed_portal_data
python manage.py runserver
```

Acces utiles:
- Public: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Back-office Django: [http://127.0.0.1:8000/dj-admin/](http://127.0.0.1:8000/dj-admin/)
- Admin fonctionnel: [http://127.0.0.1:8000/admin/validation](http://127.0.0.1:8000/admin/validation)

## Comptes de demonstration

- `national_admin` / `Admin12345!`
- `prov_admin_kin` / `Admin12345!`
- `inst_editor` / `Editor12345!`
- `inst_reader` / `Reader12345!`

## Couverture MVP

- Pages publiques: accueil, carte nationale interactive, actualites, infrastructures, zones, documentation, contact/support/signalement
- Portail institutionnel: login, dashboard, catalogue des donnees, soumissions de changement, historique
- Administration: utilisateurs, validation des soumissions, parametrage des couches, journal d'audit
- API carte: `GET /api/map/features` (filtres par couche et zone)
- RBAC + audit logging (connexions, soumissions, validations, actions d'administration)
