```md
# Spécification (Markdown) — Site Web SIG : Cartographie des infrastructures publiques (RDC)

> Source : TDR + proposition d’arborescence fournis par ARPTC :contentReference[oaicite:0]{index=0}

## 1) Contexte & finalité
La RDC fait face à un déficit de centralisation, fiabilité et mise à jour des données relatives aux infrastructures d’utilité publique (électricité, eau, fibre, voirie, assainissement). Le site/plateforme vise à réduire les conflits d’occupation du domaine public, les dégradations d’ouvrages, les surcoûts de travaux répétitifs et les risques de sécurité, via une plateforme SIG nationale sécurisée et interopérable.

## 2) Objectif général
Mettre en place une plateforme web nationale de type SIG, sécurisée et interopérable, permettant la **cartographie**, la **consultation** et la **mise à jour coordonnée** des infrastructures de génie civil et d’utilité publique sur l’ensemble du territoire.

## 3) Objectifs spécifiques
- Centraliser les données géospatiales des infrastructures publiques
- Faciliter la planification et la coordination des travaux de génie civil
- Offrir un outil commun de référence (ministères, services publics, ETD, entreprises publiques)
- Permettre la mise à jour **contrôlée** par institutions habilitées (workflow de validation)
- Garantir sécurité, confidentialité et intégrité des données sensibles
- Contribuer à la protection du domaine public et à la durabilité des infrastructures

## 4) Portée (phases)
- **Phase pilote** : 1+ villes (ex. Kinshasa / chef-lieu provincial)
- **Phase extension** : provinces + territoire national

## 5) Publics cibles & rôles (RBAC)
### 5.1 Types d’utilisateurs
- **Grand public** : consultation (lecture) + carte synthétique + actualités + documentation publique + contact
- **Partenaires institutionnels** : accès sécurisé, tableau de bord, mise à jour de données, historique
- **Administrateurs** : gestion utilisateurs, validation des données, paramétrage couches, journal accès/actions

### 5.2 Rôles (proposition)
- `PUBLIC_READER` : lecture pages publiques + carte synthétique / couches non sensibles
- `INSTITUTION_READER` : lecture étendue (selon droits)
- `INSTITUTION_EDITOR` : soumettre des mises à jour (création/édition) -> statut “en attente”
- `PROVINCIAL_ADMIN` : valider au niveau province (si applicable)
- `NATIONAL_ADMIN` : administration globale, validation finale, paramétrage, audit

> Tous les accès authentifiés doivent être journalisés (connexion, consultation, création, modification, validation).

## 6) Infrastructures couvertes (couches SIG)
- Électricité : lignes, postes, câbles souterrains
- Eau potable & assainissement : réseaux, stations, réservoirs, égouts
- Fibre optique / Télécom : fibre, antennes, centres de communication
- Voirie : routes, ponts, tunnels, ouvrages
- Caniveaux & drainage : canaux, drains, dalots, zones à risque

## 7) Arborescence / IA (Information Architecture)
### 7.1 Menu principal (public)
1. **Accueil**
   - Présentation de la plateforme
   - Carte nationale synthétique (interactive)
   - Actualités / mises à jour récentes
2. **Cartographie des infrastructures**
   - Électricité
   - Eau potable & assainissement
   - Fibre optique / télécommunications
   - Voirie
   - Caniveaux & drainage
3. **Consultation par zone**
   - Par province
   - Par ville / commune
   - Par axe / quartier
4. **Documentation**
   - Guide d’utilisation
   - Normes de saisie des données
   - Références techniques & légales
5. **Contact & assistance**
   - Support technique
   - Signalement d’anomalies
   - Coordonnées institutionnelles
6. **Accès institutionnel** (portail sécurisé)
   - Connexion
   - Tableau de bord
   - Mise à jour des données
   - Historique des modifications
7. **Administration** (accès restreint)
   - Gestion des utilisateurs
   - Validation des données
   - Paramétrage des couches cartographiques
   - Journal des accès & actions

## 8) Routes/Pages (contrat d’implémentation)
> Exemple de routes (adaptables au framework choisi)

### Public
- `/` : Accueil
- `/map` : Carte nationale synthétique (entrée rapide)
- `/actualites` : liste actualités
- `/actualites/:slug` : détail actualité
- `/infrastructures/electricite`
- `/infrastructures/eau-assainissement`
- `/infrastructures/fibre-telecom`
- `/infrastructures/voirie`
- `/infrastructures/caniveaux-drainage`
- `/zones/provinces` ; `/zones/provinces/:id`
- `/zones/villes` ; `/zones/villes/:id`
- `/zones/axes` ; `/zones/axes/:id`
- `/documentation` ; `/documentation/guide` ; `/documentation/normes` ; `/documentation/references`
- `/contact` ; `/support` ; `/signalement`

### Auth (institutionnel)
- `/auth/login`
- `/institution/dashboard`
- `/institution/data` (liste/filtre)
- `/institution/data/new` (soumission)
- `/institution/data/:id/edit` (soumission de modification)
- `/institution/history` (historique + recherche)

### Admin
- `/admin/users`
- `/admin/validation` (file d’attente)
- `/admin/layers` (config couches/symbologie/attributs)
- `/admin/audit` (journal)

## 9) Spécifications fonctionnelles (par grands modules)

### 9.1 Module Cartographie (cœur)
**But** : afficher des cartes interactives multi-couches avec filtres et fiches techniques.

#### Exigences
- Carte interactive multi-couches (au moins 5 couches principales)
- Affichage différencié par type d’infrastructure (symbologie)
- Recherche :
  - par zone (province/ville/commune/quartier)
  - par axe routier / corridor
  - par infrastructure (ID, nom, type)
- Fiche technique (panneau latéral ou modal) :
  - attributs de base (nom, type, propriétaire/gestionnaire, statut, date MAJ, etc.)
  - métadonnées (source, institution, précision, date de collecte)
- Outils carte (minimum) :
  - zoom +/-, plein écran
  - géolocalisation (si autorisée)
  - sélection par clic
  - légende dynamique
  - export “vue” (image/PDF) **optionnel**
- Gestion des performances :
  - clustering ou simplification si forte densité
  - pagination/chargement progressif des features

#### Données SIG (formats)
- Import institutionnel (ex. GeoJSON, Shapefile, CSV géocodé) — selon capacité
- Stockage dans une base géospatiale (ex. PostGIS)

### 9.2 Consultation par zone
**But** : navigation guidée par entité géographique.
- Sélecteurs (province -> ville/commune -> axe/quartier)
- Résultats : carte + liste des infrastructures dans la zone + filtres par type
- KPIs simples (optionnel) : nombre d’objets par couche, dernières mises à jour

### 9.3 Actualités / mises à jour
- CRUD actualités (admin)
- Public : liste + détail
- Champs : titre, contenu, tags, date publication, auteur, pièces jointes (optionnel)

### 9.4 Portail institutionnel (espace sécurisé)
#### Connexion
- Authentification sécurisée (mot de passe fort + MFA/2FA **recommandé**)
- Gestion de session (expiration, révocation)

#### Tableau de bord institutionnel
- Résumé : contributions récentes, éléments en attente, éléments validés/refusés
- Indicateurs : #soumissions, #validations, #rejets, dernières actions

#### Mise à jour des données (workflow)
- Un `INSTITUTION_EDITOR` peut :
  - créer un nouvel objet d’infrastructure
  - proposer une modification d’un objet existant
- Chaque soumission crée un **enregistrement de changement** :
  - statut : `DRAFT` → `SUBMITTED` → `APPROVED` / `REJECTED`
  - commentaire obligatoire au moment de la soumission
  - justificatifs/attachments (optionnel)

#### Historique des modifications
- Filtrer par : période, couche, statut, utilisateur
- Voir le “diff” (avant/après) des attributs + géométrie (si modifiée)
- Export CSV/PDF (optionnel)

### 9.5 Administration (accès restreint)
#### Gestion des utilisateurs
- CRUD comptes
- Rôles + périmètre géographique (national/province/ville)
- Activation/désactivation
- Reset mot de passe

#### Validation des données
- File d’attente des soumissions
- Validation hiérarchisée (si activée) :
  - niveau provincial puis national
- Actions : approuver / rejeter / demander correction
- Journaliser décision + commentaire

#### Paramétrage couches cartographiques
- Activer/désactiver couche
- Définir symbologie, style, champs visibles
- Définir champs obligatoires par couche
- Définir règles de confidentialité :
  - champs masqués au public
  - accès par rôle

#### Journal des accès & actions (audit)
- Connexions, lectures sensibles, créations/modifications, validations
- Recherche + export

## 10) Modèle de données (minimum viable)
### 10.1 Entités principales
- `User` : id, nom, email, institution, rôle, périmètre, statut
- `Institution` : id, nom, type, contacts
- `Layer` : id, nom, type infra, configuration (symbologie, champs)
- `InfrastructureFeature` :
  - id unique
  - layer_id
  - geometry (Point/LineString/Polygon)
  - properties (JSON) : attributs métier
  - sensitivity_level (public/restricted)
  - created_at, updated_at
- `ChangeRequest` :
  - id
  - feature_id (nullable si création)
  - action (create/update/delete)
  - proposed_geometry + proposed_properties
  - status (draft/submitted/approved/rejected)
  - submitted_by, reviewed_by
  - review_comment
  - timestamps
- `NewsPost`
- `SupportTicket` / `AnomalyReport`
- `AuditLog` : actor, action, target, metadata, ip, timestamp

## 11) Sécurité & gouvernance des données (exigences non négociables)
- Hébergement sécurisé (infra nationale ou cloud certifié)
- Chiffrement des données sensibles (au repos + en transit TLS)
- Authentification forte (MFA recommandé)
- Contrôle d’accès strict par rôles + périmètre
- Journalisation complète (accès + actions)
- Sauvegardes régulières + plan de continuité (PCA/PRA)
- Conformité aux orientations nationales cybersécurité & protection des données publiques

## 12) Exigences non fonctionnelles
- **Interopérabilité** : standards ouverts SIG (WMS/WFS/GeoJSON), API REST
- **Performance** : temps d’affichage carte acceptable même avec volumétrie élevée (tuiles, caching)
- **Responsive** : utilisable sur desktop/tablette (mobile en lecture au minimum)
- **Accessibilité** : contrastes, navigation clavier (au moins pages publiques)
- **Traçabilité** : aucune modification de données sans piste d’audit
- **Observabilité** : logs applicatifs + métriques (optionnel mais recommandé)

## 13) UX/UI (principes)
- Navigation simple, centrée sur la carte
- Légende toujours accessible
- Filtres visibles (type d’infrastructure, zone, statut)
- Panneau “détails” standardisé pour toutes les couches
- Espace institutionnel et admin visuellement distincts (bannières / couleurs / badges)

## 14) Critères d’acceptation (exemples)
- Le public peut consulter la carte nationale + couches autorisées + rechercher par zone
- Un éditeur institutionnel peut soumettre une création/modification avec commentaire
- Un admin peut valider/rejeter une soumission et la décision est journalisée
- L’historique permet de retrouver qui a modifié quoi, quand, et pourquoi
- Les couches et champs sensibles ne sont pas exposés au public
- Sauvegarde + restauration testée (preuve via rapport)

## 15) Livrables attendus
- Document de conception fonctionnelle & technique
- Plateforme web opérationnelle
- Base de données géospatiale structurée
- Guides utilisateur & administrateur
- Rapport de tests + sécurité
- Rapport final de mise en œuvre

---

## Annexes (pour Codex / équipe dev)
### A) Checklist “MVP”
- [ ] Accueil + carte synthétique
- [ ] 5 pages “Infrastructures” (1 par couche)
- [ ] Consultation par zone (province + ville/commune)
- [ ] Auth + Dashboard institutionnel
- [ ] Soumission de changements + file d’attente validation
- [ ] Admin : users + validation + audit
- [ ] Audit log partout + RBAC
- [ ] Import initial données (au moins GeoJSON)

### B) Permissions (résumé)
- Public : read(public_layers)
- Institution Reader : read(extended_layers_by_scope)
- Institution Editor : create/update -> change_request(submit)
- Provincial Admin : approve(scope=province)
- National Admin : approve(all) + manage(users/layers/audit)

### C) États d’une soumission
`DRAFT -> SUBMITTED -> (APPROVED | REJECTED | NEEDS_CHANGES)`
```
