# QA — V6.1 Terrain UX

Date : 2026-08-11

## Contrôles exécutés

- JavaScript inline validé avec `node --check`.
- Test runtime Node avec DOM minimal : chargement réel de `data.json`, `synthesis.json`, `lure_typology.json` et `tides_2026.json`.
- Hirame : rendu du pattern `Cassure → fond → pause`, combo MH et onglet Terrain vérifiés.
- Les 5 onglets Hirame ont été rendus en runtime : Terrain, Leurres, Couleurs, Animations, Comprendre.
- Les anciens libellés visibles `Essence Hirame`, `Règle de lecture`, `Rôles dans la boîte — l'essence`, `Bracketing`, `Principe :` ne sont plus présents dans les panneaux rendus.
- JSON principaux validés.
- `pipeline.py` compilé avec `py_compile`.
- Service worker passé au cache `carnet-peche-jp-v6-1-ux-20260811`.
- Les données et règles matériel V6 ne sont pas modifiées par cette passe UX.

## Note rendu graphique

L'environnement de test Chrome de ce conteneur bloque les URLs locales par politique d'organisation. La QA graphique automatisée par capture Chrome n'a donc pas été utilisée comme critère de validation. La structure DOM/CSS et le rendu logique des panneaux ont été testés directement.
