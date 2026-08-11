# QA V4 — 2026-08-11

Vérifications effectuées avant création de l'archive GitHub-ready.

## Syntaxe et formats

- `python3 -m py_compile pipeline.py` : OK
- JavaScript inline de `index.html` extrait puis `node --check` : OK
- `node --check sw.js` : OK
- Parsing JSON : `data.json`, `tides_2026.json`, `synthesis.json`,
  `lure_typology.json`, `manifest.webmanifest` : OK
- Parsing des 9 fichiers `research/*.json` : OK

## Base / export

- Schéma export : V4
- Observations validées : **493**
- Espèces documentées : **10 / 10**
- Intel destination : **257**
- Étapes du voyage : **8**
- Jours de marée embarqués : **25**
- Observations avec typologie de leurre : **101**
- Cohérence DB SQLite ↔ export JSON vérifiée : OK

## Régressions ciblées

### Import terrain contenant un tableau

Test avec :

```json
"observation": ["bait visible", "veine de courant"]
```

Résultat : les deux valeurs sont insérées comme tags séparés, sans exception.
Réimport du même fichier : détecté comme doublon, aucune seconde observation créée.

### Deep research

Réimport d'un fichier déjà présent : **0 observation / 0 intel** ajoutés.
L'idempotence par fingerprint est fonctionnelle.

### Marée

Recherche de l'ancien moteur harmonique provisoire dans l'UI : aucun reliquat de logique
`M2/S2/K1/O1` ou de constantes de démonstration.

### Fichiers servis

Test via `python3 -m http.server` : HTTP 200 pour :

- `index.html`
- `data.json`
- `tides_2026.json`
- `sw.js`
- `manifest.webmanifest`

## Sécurité de dépôt

Scan simple des motifs usuels de clés API/tokens/private keys avant packaging : aucun secret
embarqué détecté.
