# QA — V6.2 Evidence

Date de contrôle : 2026-08-11.

## Données

- `data.json` valide : **493 observations**, **10 espèces**, **8 étapes**, **2 combos**.
- `evidence_policy.version = 6.2` présent dans l'export.
- SQLite : **493 observations validées**, cohérent avec `data.json`.
- Les JSON racine et `research/` sont parsables.
- **0 recommandation active > 50 g** après export.
- Les **25 dates de séjour** sont toutes couvertes par `tides_2026.json` ; le fichier contient 27 journées au total avec les jours auxiliaires.

## Code

- `python -m py_compile pipeline.py` : OK.
- JavaScript extrait de `index.html` : `node --check` OK.
- Test runtime Node avec DOM/fetch/localStorage simulés : accueil rendu, fiche Hirame rendue, bloc « Niveau de preuve » présent, contexte Numazu actif pris en compte.

## Evidence Engine

Test Hirame avec Numazu activé :

- présence : `SOLIDE`, corpus multi-sources ;
- timing : `SIGNAL` lorsque le meilleur pattern repose sur une seule preuve contextuelle ;
- leurre : `SOLIDE` ;
- animation : `SOLIDE`, avec forte réplication technique même lorsque la localité est faible ;
- couleur : `SOLIDE` sur le meilleur groupe répliqué.

Ce test vérifie l'effet recherché des poids par facette : la localité/saison pénalisent davantage présence/timing que mécanique/animation. Une observation isolée reste plafonnée afin de ne pas devenir « très solide » sans réplication.

## UX / sémantique

Présents et vérifiés dans `index.html` :

- `Niveau de preuve de la base` ;
- `TRÈS SOLIDE / SOLIDE / SIGNAL / HYPOTHÈSE` ;
- `VALIDÉ PAR TOI` ;
- `Compatibilité conditions` séparée du niveau de preuve dans le QCM ;
- `Pourquoi ce niveau ?` avec 5 dimensions ;
- `Opportunité marée/lumière` à la place de `Score marée/lumière`.

Le score historique `confidence 0.xx` n'est plus le signal principal des observations brutes ; il est conservé en information secondaire pour la traçabilité du pipeline.
