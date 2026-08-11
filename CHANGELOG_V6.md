# Carnet Pêche JP — V6 Travel Loadout

## Matériel de voyage devient une contrainte du moteur

Deux ensembles sont désormais intégrés comme **loadout réel**, pas comme simple inventaire :

- **M** — Tenryu Injection SP 82 M Quattro + Twin Power XD 4000HG + PE0.8. Plage officielle 8–30 g.
- **MH** — Tenryu Injection SP 82 MH Quattro + Twin Power FE C5000XG + PE1.5. Plage officielle 12–45 g ; 46–50 g est une zone « haute charge » acceptée par l'utilisateur.

La page d'accueil met ces deux ensembles immédiatement après les destinations. Chaque fiche espèce affiche maintenant le combo de départ et les recommandations QCM/sourcées portent un badge M/MH.

## Filtre poids global

- `>50 g` : recommandation exclue du moteur et de l'export décisionnel.
- `46–50 g` : MH uniquement, badge **HAUTE CHARGE**.
- `31–45 g` : MH.
- `8–30 g` : M ou MH selon espèce / rôle.
- `<8 g` connu : signalé sous la plage de la M.

Le fait biologique d'une observation reste conservé quand une source utilise un leurre >50 g, mais le leurre, sa couleur et son animation ne nourrissent plus les recommandations personnelles.

Cinq références >50 g ont été supprimées de `lure_typology.json` et les synthèses Hamachi ont été réécrites pour le loadout réel.

## Log terrain

Le log téléphone enregistre maintenant :

- combo M/MH ;
- poids total lancé (optionnel) ;
- validation du plafond 50 g.

`pipeline.py import-log` conserve ces informations dans les métadonnées terrain.

## Pipeline

- schéma `data.json` : V6 ;
- `combos.setup_json` ajouté à SQLite ;
- `gear_policy` exporté dans `data.json` ;
- filtre >50 g appliqué également lors de `pipeline.py export`.
