# Changelog — V5

## Navigation marée / lumière

- Ajout de `stay_dates` par étape, limité à 4 jours.
- Les pads démarrent sur le premier jour réel du séjour et ne naviguent que dans ces dates.
- Fukuoka : 15–18/11 ; Kobe : 20–23/11 ; Numazu : 29/11–02/12 ; Tokyo : 02–05/12.
- Boutons jour + Préc./Suiv. avec score comparatif 0–100.
- Score = mouvement de phase au moment utile pour les espèces + préférences de marée présentes dans la base + marnage relatif au séjour.
- Ajout premières lueurs / lever / coucher / fin des lueurs.
- Correction du calcul du jour UTC/JST pour les événements solaires du matin.
- Courbe toujours basée uniquement sur les extrema JMA embarqués ; aucun retour au modèle harmonique placeholder.

## Destination

- La lecture principale des pads est condensée en : Tendance, Spots à lire, Marée/timing, Typicité locale.
- Les gros briefs historiques ne sont plus la lecture principale.
- Les preuves et contraintes détaillées restent disponibles sous un volet replié.

## Leurres / animations

- Ajout d'une lecture par rôle avant la fréquence des familles de leurres.
- Nouvelle grammaire d'animation : linéaire, stop-and-go, lift-and-fall, jerk/twitch, dérive, fall, one-pitch/jigging, surface dog-walk/pop/dive.
- Séparation stricte entre commande pêcheur, comportement intrinsèque du leurre et effet recherché.
- Le moteur de consensus d'action ne fusionne plus one-pitch et lift-and-fall.

## Couleurs

- Matrice clarté × lumière × activité × fourrage.
- Logique spécifique eaux claires / vertes / troubles et transitions de lumière.
- Distinction ghost, opaque/pearl, métallique/flash, fluo/UV, glow/phosphorescent et mat sombre.
- Explication rose fluo vs jaune/chartreuse.
- Méthode de color bracketing au lieu d'une “couleur magique”.
- Le QCM affiche maintenant une logique couleur contextuelle séparée des recommandations sourcées.

## Données / pipeline

- `schema_version` passe à 5.
- `trip_stops` ajoute `stay_dates_json` et `summary_json`.
- Bootstrap/export conservent ces champs.
- `synthesis.json` ajoute `technique_v5` et ses sources.
- Ajout de `research/technique_consensus_v5_sources.json`.
- Service worker V5 : nouveau cache pour forcer la mise à jour après déploiement.
