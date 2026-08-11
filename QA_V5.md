# QA — Carnet Pêche JP V5

Date : 2026-08-11

## Données

- `data.json` valide : **493 observations**, `schema_version = 5`.
- 8 étapes, chacune avec un résumé destination et 1 à 4 `stay_dates`.
- Chaque `stay_date` affichable possède une journée correspondante dans `tides_2026.json`.
- `tides_2026.json` : 25 entrées port × jour.
- Tous les JSON racine et `research/*.json` passent le parseur JSON.

## SQLite / pipeline

- `pipeline.py` compile avec `py_compile`.
- `pipeline.py export` exécuté avec succès après migration V5.
- La table `trip_stops` contient `arrival_date`, `stay_dates_json`, `summary_json`.
- Export DB → JSON conserve les dates de séjour et les résumés.

## JavaScript / interface

- JavaScript inline validé avec `node --check`.
- Test runtime avec DOM/fetch simulés : chargement des 493 observations, rendu accueil, pad Kobe, onglets Animation et Couleur.
- Test du pad Kobe : 4 jours 20→23/11 présents et scores calculés.
- Contrôle solaire Kobe 20/11/2026 : premières lueurs ~06:10, lever ~06:37, coucher ~16:52, fin des lueurs ~17:19 JST.
- Le bug de date UTC/JST sur l'aube a été détecté puis corrigé pendant cette passe.
- Les panneaux techniques contiennent bien des mécaniques distinctes `Linéaire` et `Lift-and-fall`.
- La logique couleur contient ghost/transparent, opaque/pearl, flash, fluo/UV, glow et silhouette sombre.

## HTTP / PWA

Serveur local `python3 -m http.server` : HTTP 200 vérifié pour :

- `index.html`
- `data.json`
- `tides_2026.json`
- `synthesis.json`
- `sw.js`

Le cache du service worker est versionné `carnet-peche-jp-v5-20260811`.

## Limites assumées

- Le score marée/lumière est un **comparateur** entre jours du séjour, pas une probabilité de capture.
- L'interpolation JMA ne modélise pas le courant hydrodynamique réel d'un poste.
- Les grandes synthèses narratives historiques ne sont pas réécrites ; la nouvelle couche technique V5 est séparée.
- Madai, Saba, Aji et Mebaru ont encore trop peu d'observations techniques pour imposer une doctrine leurre/couleur ; l'interface le dit au lieu d'inventer.
