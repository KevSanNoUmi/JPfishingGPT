# Changelog — V4 (2026-08-11)

## Correctifs

- Correction de l'import des sessions terrain contenant des tags tableau.
- Déduplication des imports terrain et research par fingerprint.
- Conservation de `arrival_date` lors des exports.
- Conservation des métadonnées, niveaux de preuve et typologies de leurres.
- Correction du double avancement possible du QCM lors du retour asynchrone de pression.
- Dates/heures des logs enregistrées en heure du Japon + timestamp UTC.
- Chargement des données rendu explicite en cas d'échec.
- Échappement HTML renforcé sur les principales surfaces de contenu dynamique.
- Service worker V4 : précache des données critiques et repli offline fiable.

## Marées

- Suppression totale des constantes harmoniques provisoires de la V3.
- Ajout de `tides_2026.json` avec 25 journées de PM/BM embarquées.
- Couverture : Shimizu, Hakata/Fukuoka, référence Hakata pour Itoshima, Kobe, Toba
  (proxy Ise-Shima), Uchiura/Numazu, Tokyo et Kashima.
- L'app n'affiche plus de marée calculée lorsqu'aucune table officielle n'est disponible.

## Données

- Base exportée : **493 observations validées**.
- Espèces documentées : Hirame, Suzuki, Hamachi, Aori-Ika, Kurodai, Madai, Tachiuo, Saba, Aji, Mebaru.
- **257 entrées d'intel destination** stockées en base.
- **101 observations** avec typologie de leurre dans l'export courant.
- Import des deep-research Fukuoka, Kobe, Ise-Shima et Numazu.
- Enrichissements complémentaires Shizuoka, Tokyo et Kashima.

## Voyage

8 pads de voyage configurés :

1. Shizuoka surf — 7 novembre 2026
2. Fukuoka — 15 novembre 2026
3. Shikanoshima / Itoshima — 17 novembre 2026
4. Kobe / Akashi — 22 novembre 2026
5. Ise-Shima / Mie — 27 novembre 2026
6. Numazu / Izu — 29 novembre 2026
7. Tokyo — 2 décembre 2026
8. Kashima — 4 décembre 2026

## Pipeline

Nouvelles commandes :

```text
bootstrap-json
import-research
brief-local
```

`export` génère désormais `data.json` et `tides_2026.json`.
