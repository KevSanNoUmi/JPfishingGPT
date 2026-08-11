# Carnet Pêche JP — V4

PWA mobile-first de préparation et de décision pour un voyage de pêche du bord au Japon.
Le dépôt contient à la fois l'application statique publiée sur GitHub Pages, la base SQLite
qui sert de source de vérité et le pipeline Python d'enrichissement/export.

## État de cette release

- **493 observations validées** dans `data.json`, sur les 10 espèces de la base désormais documentées.
- **257 entrées d'intelligence locale** liées aux étapes du voyage (accès, stratégie,
  conditions, contexte et signaux terrain), intégrées dans les pads d'étape.
- **8 étapes de voyage** avec date d'arrivée et espèces cibles.
- **25 journées de marées astronomiques JMA** embarquées dans `tides_2026.json` pour les
  dates utiles du voyage.
- **101 observations enrichies par une typologie de leurre** dans l'export courant.
- Les quatre deep-research fournis pour Fukuoka, Kobe, Ise-Shima et Numazu sont conservés
  dans `research/` avec les enrichissements complémentaires Shizuoka, Tokyo et Kashima.

## Ce qui change en V4

### 1. Marées : suppression du faux modèle harmonique

La V3 affichait une courbe calculée à partir de constantes harmoniques provisoires. Elles
étaient explicitement des placeholders et pouvaient produire une heure crédible mais fausse.
La V4 ne fait plus cela.

`tides_2026.json` embarque les **heures de pleine mer / basse mer issues des prévisions
astronomiques JMA** pour les dates prévues du voyage. L'app :

- détermine `montante / descendante / étale` depuis les extrema officiels ;
- affiche PM/BM et leurs hauteurs ;
- dessine uniquement une interpolation visuelle entre ces points ;
- n'invente rien lorsqu'une date n'est pas couverte ;
- affiche clairement les références de proximité lorsqu'elles sont utilisées
  (`Hakata` pour Itoshima, `Toba` pour Ise-Shima).

**Important :** ce sont des prévisions astronomiques, pas des hauteurs observées en temps
réel. Vent, pression, houle et configuration locale peuvent modifier le niveau réel.

### 2. Log terrain fiabilisé

L'import d'une session PWA ne casse plus lorsque le QCM contient plusieurs observations du
spot. Les valeurs tableau sont maintenant éclatées proprement en tags. L'import est aussi
idempotent grâce à un fingerprint : réimporter le même fichier ne duplique pas la session.

L'app enregistre en plus :

- la date/heure locale `Asia/Tokyo` ;
- un timestamp UTC séparé ;
- une copie figée des conditions du QCM ;
- les métadonnées complètes de la session.

### 3. Pipeline et schéma synchronisés

La V4 ajoute au schéma :

- `trip_stops.arrival_date` ;
- `sources.source_kind` ;
- `observations.evidence_level`, `metadata_json`, `typology_json`, `fingerprint` ;
- `trip_intel` pour les règles d'accès / stratégie / contexte ;
- `tide_days` pour les tables de marée embarquées.

Un nouvel export ne supprime donc plus silencieusement les dates d'arrivée, métadonnées ou
la typologie déjà stockée.

### 4. Deep research intégré sans gonfler artificiellement la concordance

`pipeline.py import-research` distingue :

- une **preuve directe liée à une espèce** → observation ;
- une règle synthétique, réglementation, plan de voyage ou contexte général → `trip_intel` ;
- une table officielle de marée → `tide_days`.

Ainsi une synthèse dérivée ne compte pas comme une nouvelle source indépendante confirmant
une autre synthèse.

### 5. PWA offline plus robuste

Le service worker précache maintenant les fichiers indispensables (`index.html`, `data.json`,
`tides_2026.json`) dès l'installation. Les fichiers de données sont ensuite servis en
**network-first avec repli cache**. Une première installation peut donc réellement démarrer
hors ligne après que le service worker a terminé son installation.

### 6. QCM et rendu mobile

- la réponse asynchrone de pression ne peut plus faire avancer le QCM deux fois ;
- la marée n'est préremplie que si une table officielle existe pour le jour concerné ;
- les erreurs critiques de chargement ne sont plus avalées silencieusement ;
- plusieurs surfaces de rendu dynamique sont échappées avant insertion HTML ;
- les pads d'étape affichent une couche d'**intel V4** sourcée en plus du brief.

## Fichiers importants

- `index.html` — PWA et interface mobile.
- `data.json` — export public des espèces, observations, leurres, combos et étapes.
- `tides_2026.json` — tables PM/BM embarquées pour le voyage.
- `synthesis.json` — synthèse éditoriale historique ; voir la note V4 dans le fichier.
- `lure_typology.json` — référentiel de typologie des leurres.
- `peche_jp.db` — base SQLite source de vérité de cette release.
- `schema.sql` — schéma V4.
- `pipeline.py` — import, enrichissement, briefs et export.
- `research/` — sources structurées utilisées pour l'enrichissement V4.
- `sw.js` — service worker offline.

## Workflow recommandé

### Installation / migration

```bash
python3 pipeline.py init
```

`init` est additif : il crée les tables manquantes et migre une base existante sans jeter les
données.

### Reconstruire la base depuis un export existant

À utiliser seulement si le `.db` est absent ou volontairement régénéré :

```bash
python3 pipeline.py bootstrap-json data.json --force
```

### Extraction classique depuis une source

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 pipeline.py add-source
python3 pipeline.py extract <source_id> source.txt
python3 pipeline.py review
python3 pipeline.py validate <observation_id>
```

### Importer un deep research structuré

```bash
python3 pipeline.py import-research research/mon_fichier.json
```

L'import est idempotent pour les observations et l'intel. Les espèces hors périmètre des 10
espèces de l'app sont conservées dans le fichier de recherche mais non injectées comme
observations.

### Retour terrain depuis le téléphone

Exporter les sessions depuis la PWA puis :

```bash
python3 pipeline.py import-log sessions-terrain.json
```

### Régénérer les briefs locaux et publier

```bash
python3 pipeline.py brief-local
python3 pipeline.py export
```

`export` régénère **à la fois** `data.json` et `tides_2026.json`.

Le brief Claude historique reste disponible avec :

```bash
python3 pipeline.py brief
```

mais il n'est pas nécessaire pour publier la couche d'intel V4 déterministe.

## Vocabulaire contrôlé du QCM

Ne pas dériver ces valeurs :

- `maree` : `montante`, `descendante`, `étale`
- `moment_jour` : `aube`, `jour`, `crépuscule`, `nuit`
- `couleur_eau` : `claire`, `trouble`, `verte`
- `pression_atmo` : `basse`, `moyenne`, `haute`

La pression récupérée par l'app est classée ainsi : `<1013` basse, `1013–1020` moyenne,
`>1020` haute.

## Tester localement

Ne pas ouvrir `index.html` directement en `file://`, car la PWA charge des JSON avec `fetch`.
Servir le dossier :

```bash
python3 -m http.server 8000
```

puis ouvrir `http://localhost:8000/`.

Pour tester l'offline dans un navigateur desktop : charger une fois la page, attendre
l'activation du service worker, puis passer DevTools > Network en Offline et recharger.

## Déploiement GitHub Pages

Le contenu de ce dossier peut être placé directement à la racine du dépôt :

```bash
git add .
git commit -m "Carnet Peche JP V4"
git push
```

Avec GitHub Pages configuré sur la branche `main` et `/root`, aucune étape de build n'est
nécessaire.

Sur iPhone, après le déploiement, ouvrir le site dans Safari puis **Partager → Sur l'écran
d'accueil**. Si une ancienne V3 reste affichée, fermer/réouvrir la PWA ; au besoin supprimer
l'ancienne icône et la réinstaller pour repartir avec le nouveau service worker.

## Note sur `synthesis.json`

La base opérationnelle est désormais à 493 observations, mais les grands paragraphes de
`synthesis.json` restent la synthèse éditoriale V3 initialement produite sur 303 observations.
Ils sont volontairement conservés pour éviter de prétendre qu'ils ont été recalculés. Les
nouvelles observations alimentent bien les fiches/QCM et l'intel destination. Une prochaine
étape pourra régénérer cette couche narrative sur l'ensemble de la V4.
