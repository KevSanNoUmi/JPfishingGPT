# QA — Carnet Pêche JP V6 Travel Loadout

Date : 2026-08-11

## Intégrité données

- `data.json`, `synthesis.json`, `lure_typology.json`, `tides_2026.json` et `manifest.webmanifest` : JSON valides.
- Schéma export : **V6**.
- **493 observations validées**, **10 espèces documentées**, **257 éléments d'intelligence locale**, **8 étapes**.
- SQLite : 493 observations et 2 combos ; colonne `combos.setup_json` présente.
- Les 25 journées nécessaires aux `stay_dates` des 8 étapes ont une table de marée embarquée.

## Loadout

- M : SP82M Quattro · Twin Power XD 4000HG · PE0.8 · 8–30 g nominal.
- MH : SP82MH Quattro · Twin Power FE C5000XG · PE1.5 · 12–45 g nominal · plafond utilisateur 50 g.
- L'accueil affiche les 2 combos ; les fiches espèce affichent le combo de départ ; les recommandations sourcées/QCM affichent le badge M/MH.
- Le journal terrain stocke `combo` et `cast_weight_g`.

## Filtre 50 g

- `lure_typology.json` : **51 entrées**, poids maximal actif **50 g**, aucune entrée >50 g.
- `data.json` : **0 recommandation active connue >50 g**.
- Poids maximal connu parmi les recommandations exportées actuelles : **48 g**.
- **6 observations** utilisant un leurre >50 g ont conservé leur fait biologique mais leur recommandation a été retirée et marquée `gear_filter.excluded_recommendation`.
- Les références lourdes supprimées de la typologie active ne figurent plus dans la synthèse décisionnelle Hamachi.
- L'interface affiche « leurre hors setup » lorsqu'une observation brute conservée provient d'une recommandation >50 g.

## Pipeline terrain

Test effectué sur une copie de la base :

- session avec réponse QCM multiple (array) : import OK ;
- combo MH + poids total 48 g : import/export OK, `cast_weight_g: 48` conservé dans la recommandation ;
- session >50 g : le fait terrain est importé, la recommandation leurre n'est pas exportée ;
- second import du même fichier : doublon détecté, 0 nouvel import.

## Code / PWA

- `python -m py_compile pipeline.py` : OK.
- JavaScript inline extrait de `index.html` puis `node --check` : OK.
- Service worker : cache V6 dédié `carnet-peche-jp-v6-20260811`; fichiers critiques `index.html`, `data.json`, `tides_2026.json` précachés.
- Test visuel mobile effectué sur accueil et fiche Hirame : 2 cartes loadout visibles, 10 espèces présentes, fiche Hirame avec MH principal et M en alternative.

## Limites assumées

- Le plafond 50 g est une contrainte utilisateur. La SP82MH reste donnée fabricant pour 12–45 g ; 46–50 g est donc signalé « haute charge », jamais « plage nominale ».
- Une observation >50 g peut rester lisible comme donnée biologique/comportementale ; elle ne contribue pas aux recommandations personnelles de leurre/couleur/animation.
- Les poids non connus restent marqués « poids à vérifier » : le moteur ne les invente pas.
