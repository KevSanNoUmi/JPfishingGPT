# V6.1 — Terrain UX

## Objectif

Transformer les fiches espèce d'une base de connaissance visible en un outil de décision lisible au bord de l'eau.

## Changements

- Suppression des grands fonds ambre/marron dans les fiches : les cartes sont à nouveau bleu nuit, l'ambre n'est utilisé que pour les signaux et priorités.
- Remplacement de l'intitulé « Essence » par un pattern opérationnel très court.
- Onglets renommés : Terrain / Leurres / Couleurs / Animations / Comprendre.
- Nouveau plan Terrain : Où, Quand, Combo, Leurre/rôle, Comment, Couleur de départ, Si ça ne donne rien.
- QCM « config du moment » et journal terrain intégrés au premier niveau Terrain.
- Leurres : lecture par rôle à remplir sur le spot avant famille/densité/modèle.
- Animations : chaque mécanique sépare explicitement geste du pêcheur, comportement du leurre et effet recherché. Les mécaniques les plus pertinentes à l'espèce sont affichées en premier.
- Couleurs : logique de signal, diagnostic suivi/refus vs absence de contact, matrice de départ et distinction rose/magenta vs jaune/chartreuse.
- Comprendre : comportement, synthèse longue, divergences et observations brutes restent disponibles mais repliés.
- Cache PWA incrémenté pour forcer la nouvelle interface après déploiement.

## Invariants conservés

- 493 observations.
- Plafond projet : 50 g maximum.
- M = SP82M Quattro + Twin Power XD 4000HG + PE0.8.
- MH = SP82MH Quattro + Twin Power FE C5000XG + PE1.5, 46–50 g en haute charge utilisateur.
- Dates de séjour et tables de marée V5.1/V6 inchangées.
