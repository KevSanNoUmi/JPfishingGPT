# QA — V5.1

- Itinéraire contrôlé dans SQLite et `data.json` : Fukuoka 15–18/11, Kobe 21–24/11, Ise-Shima 26–28/11, Numazu 29/11–01/12, Tokyo 02–05/12.
- Toutes les dates de ces séjours ont une table de marée embarquée pour le port/référence du pad.
- Ajouts officiels : Kobe 24/11 (JMA KB) et Toba 26/11 (JMA TB, proxy régional Ise-Shima).
- Le bloc `Prévisions marée` est le premier contenu d’un pad ouvert ; la courbe est placée avant navigation, score, extrema et soleil.
- `Lecture destination` est séparée visuellement sous le bloc marée.
- `pipeline.py` compile ; tous les JSON chargent ; JavaScript inline et service worker passent `node --check`.
- Serveur HTTP local : `index.html`, `data.json` et `tides_2026.json` répondent correctement.
- Cache PWA incrémenté en V5.1 pour éviter qu’un téléphone conserve l’ancien ordre d’affichage.
