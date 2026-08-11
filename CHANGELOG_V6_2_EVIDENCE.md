# Changelog — V6.2 Evidence

## Objectif

Faire de la traçabilité une partie du moteur de décision sans transformer l'interface en tableau statistique. La V6.2 sépare ce qui semble être une bonne opportunité de pêche de la solidité des preuves utilisées pour recommander une action.

## Moteur de preuve

- Ajout des niveaux **TRÈS SOLIDE / SOLIDE / SIGNAL / HYPOTHÈSE**.
- Ajout d'une couche séparée **VALIDÉ PAR TOI** pour les sessions PWA réimportées.
- Évaluation sur cinq axes : localité, saison, observation/directivité, réplication indépendante et compatibilité setup.
- Réplication calculée par sources **et par origines** afin de ne pas survaloriser plusieurs contenus issus du même site/magasin/fabricant.
- Plafond de niveau appliqué aux observations isolées : une preuve unique ne peut pas devenir « très solide » uniquement parce qu'elle est locale et datée exactement.
- Poids contextuels : localité/saison pèsent plus pour présence/timing ; directivité/réplication/setup pèsent plus pour leurres et animations.

## Terrain

- Le plan de jeu affiche une synthèse de preuve par facette : présence, timing, leurre, animation, couleur.
- Si un port est activé avec « Pêcher ici », les dimensions localité et saison sont recalculées par rapport à la destination et aux vraies dates du séjour.
- Le moteur ne transforme pas un niveau de preuve en probabilité de capture.

## QCM

- La compatibilité aux conditions du moment est affichée séparément du niveau de preuve.
- À égalité de compatibilité, les recommandations les mieux étayées passent devant.
- « Pourquoi ce niveau ? » affiche les cinq dimensions, le nombre d'observations, de sources et d'origines, puis le maillon faible.

## Comprendre

- Distinction visible entre **Observation / Pattern / Hypothèse / Ton terrain**.
- Les observations brutes n'affichent plus le score historique 0.xx comme signal principal ; il reste disponible en information secondaire.

## Destination / marée

- « Score marée/lumière » devient **Opportunité marée/lumière** pour éviter toute confusion avec la solidité documentaire.
- Les preuves/contraintes destination remplacent le niveau numérique 1–4 exposé à l'utilisateur par des libellés lisibles : preuve directe, signal local, indice, contexte.

## Données / pipeline

- `data.json` exporte désormais `evidence_policy` avec la version du moteur et ses principes.
- `schema_version` reste à 6 pour compatibilité ; le moteur d'évidence porte sa propre version `6.2`.
- Aucune observation, date de séjour, marée, combo ou règle poids n'est supprimée.
