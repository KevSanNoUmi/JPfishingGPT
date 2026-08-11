# Carnet Pêche JP — V6 Travel Loadout

PWA mobile-first de préparation et de décision pour un voyage de pêche du bord au Japon.
Le dépôt contient l'application GitHub Pages, la base SQLite source de vérité, les données
exportées et le pipeline Python d'enrichissement.

## État de la release

- **493 observations validées** sur **10 espèces**.
- **257 éléments d'intelligence locale** rattachés aux étapes du voyage.
- **8 étapes** avec jours de séjour explicites (maximum 4 jours affichés par pad).
- **25 journées de marées astronomiques JMA** embarquées dans `tides_2026.json`.
- **96 recommandations actives** enrichies par une typologie de leurre après application du plafond 50 g.
- Deep research conservé dans `research/` pour Fukuoka, Kobe, Ise-Shima, Numazu, plus les
  compléments Shizuoka, Tokyo, Kashima, Madai et Saba.

## Ce qui change en V6


### 0. La valise devient le filtre principal

Le moteur raisonne maintenant avec les **deux ensembles réellement emportés** :

- **M** — Tenryu Injection SP 82 M Quattro + Twin Power XD 4000HG + PE0.8. Plage officielle 8–30 g. Rôle : contrôle, dérive, précision, stop/restart.
- **MH** — Tenryu Injection SP 82 MH Quattro + Twin Power FE C5000XG + PE1.5. Plage officielle 12–45 g. Rôle : puissance, distance, courant, fond. L'utilisateur accepte 46–50 g en **haute charge**, avec un plafond absolu à 50 g.

Règle globale : **aucun leurre >50 g n'entre dans les recommandations, consensus, QCM ou typologies actives**. Quand une bonne source utilise 65–80 g, le fait biologique peut être conservé (courant, couche, timing, comportement), mais la recommandation de leurre est retirée du moteur personnel.

Les fiches espèce et la config du moment affichent désormais le combo M/MH avant le leurre. Le journal terrain stocke aussi le combo et le poids total lancé.

### 1. Navigation marée limitée aux vrais jours sur place

Chaque pad destination possède maintenant `stay_dates`. L'écran marée commence au **premier
jour du séjour** et permet de naviguer avec **Préc. / Suiv.** uniquement dans ces dates,
avec un maximum de quatre jours affichés.

Pour Fukuoka, Kobe et Numazu, les plages suivent directement les dates des deep research :
15–18 novembre, 21–24 novembre et 29 novembre–1er décembre. Ise-Shima couvre 26–28 novembre et Tokyo 2–5 décembre.

Chaque jour affiche :

- les PM/BM et hauteurs JMA embarquées ;
- la courbe interpolée du jour ;
- les **premières lueurs**, le lever, le coucher et la fin des lueurs ;
- les croisements faible lumière × phase de marée active ;
- un **score comparatif 0–100** pour classer les jours du séjour.

Le score combine : activité de phase autour des moments documentés pour les espèces ciblées,
préférences de marée présentes dans la base et marnage relatif entre les jours du séjour.
Il sert à **comparer les journées entre elles**. Ce n'est ni une probabilité de capture, ni un
modèle hydrodynamique du courant réel d'une pointe, d'un chenal ou d'un port.

### 2. Brief destination condensé

Les gros blocs de texte ont été remplacés en lecture principale par quatre informations :

- **Tendance** : ce qui structure la pêche locale.
- **Spots à lire** : secteurs précis et ce qu'il faut y observer.
- **Marée / timing** : fenêtre et logique utiles sur place.
- **Typicité locale** : bait, structure, pression, mobilité, lumière ou autre particularité.

Les preuves détaillées restent accessibles dans un volet replié pour ne pas perdre la
traçabilité.

### 3. Consensus leurres : raisonner par rôle

L'onglet leurres commence maintenant par le **rôle à remplir** avant d'afficher les fréquences
par famille/densité : chercher loin et tenir bas, insister précisément, pêcher le vent,
présenter dans une veine, induction surface, etc.

Le but est d'éviter qu'un nom de modèle devienne une recette universelle. La famille, la
densité, la taille, la vitesse et la couche sont reliées à une fonction de pêche.

### 4. Grammaire stricte des animations

V5 sépare explicitement :

1. **ce que fait le pêcheur** — moulinet, canne, gestion de bannière ;
2. **ce que fait le leurre** — roll, wobble, tail swing, dart, shimmy, planing… ;
3. **l'effet recherché** — tenir une couche, provoquer, dériver, créer une retombée, etc.

Les mécaniques ne sont plus mélangées :

- linéaire ;
- stop-and-go ;
- lift-and-fall ;
- jerk / twitch ;
- dérive / dead drift ;
- fall / chute ;
- one-pitch / jigging ;
- surface : dog-walk / pop / dive.

Exemple : un **linéaire** laisse la conception du leurre produire sa nage via la récupération ;
un **lift-and-fall** crée volontairement une montée à la canne puis une retombée. Une pause
dans un linéaire produit un stop-and-go, pas automatiquement un lift-and-fall.

### 5. Couleurs : une logique de visibilité, pas une couleur magique

L'onglet couleur commence par quatre axes :

- clarté / teinte de l'eau ;
- lumière ;
- niveau d'activité / pression ;
- fourrage identifié ou non.

La matrice V5 distingue notamment naturel/ghost, translucide, métallique/flash, opaque,
mat/silhouette, pearl, UV/glow et couleurs high-appeal.

Le **rose fluo** et le **jaune/chartreuse** sont traités comme deux solutions de visibilité,
pas comme des lois : rose très distinctif dans des eaux verdâtres/bleutées et aux transitions
de lumière ; jaune/chartreuse très lisible en eau chargée ou lumière diffuse. Quand le bait
est clairement identifié et que les poissons nourrissent dessus, la silhouette/taille puis
le naturel/flash peuvent redevenir prioritaires.

La méthode recommandée est un **color bracketing** : choix logique de départ, une option plus
discrète, une option plus visible, puis modification d'une seule variable à la fois.

### 6. Sources techniques de la passe V5

La structuration technique recoupe les 493 observations avec des documents fabricants et des
articles techniques, notamment DAIWA Overdrive, Megabass KAGELOU, le guide eging YAMARIA et
les dossiers couleur/animation Ultimate Fishing. La provenance est conservée dans
`synthesis.json` et `research/technique_consensus_v5_sources.json`.

## Marées et soleil

`tides_2026.json` contient les extrema astronomiques JMA. La courbe de l'app est une
**interpolation visuelle entre ces extrema**, pas une reconstruction harmonique. Une référence
de proximité est signalée lorsqu'elle est utilisée (par exemple Hakata pour Itoshima ou Toba
pour Ise-Shima).

Les horaires de lumière sont calculés localement pour les coordonnées du port : crépuscule
civil du matin (premières lueurs), lever, coucher et crépuscule civil du soir. Ils donnent une
fenêtre opérationnelle plus utile au pêcheur que le seul lever/coucher.

## Pipeline / schéma V6

`trip_stops` conserve désormais :

- `arrival_date` ;
- `stay_dates_json` ;
- `summary_json` ;
- les espèces cibles, port et briefs existants.

Le schéma ajoute `combos.setup_json` pour conserver canne, moulinet, PE, plages de lancer et rôle. Le reste des migrations V4/V5 est conservé : métadonnées observations, fingerprint terrain,
`trip_intel`, typologie, `tide_days`, etc.

### Installation / migration

```bash
python3 pipeline.py init
```

### Importer un deep research structuré

```bash
python3 pipeline.py import-research research/mon_fichier.json
```

### Retour terrain depuis le téléphone

```bash
python3 pipeline.py import-log sessions-terrain.json
```

### Régénérer et publier

```bash
python3 pipeline.py brief-local
python3 pipeline.py export
```

`export` régénère `data.json` et `tides_2026.json` en conservant les jours de séjour et les
résumés destination.

## Vocabulaire contrôlé du QCM

- `maree` : `montante`, `descendante`, `étale`
- `moment_jour` : `aube`, `jour`, `crépuscule`, `nuit`
- `couleur_eau` : `claire`, `trouble`, `verte`
- `pression_atmo` : `basse`, `moyenne`, `haute`

## Tester localement

```bash
python3 -m http.server 8000
```

Puis ouvrir `http://localhost:8000/`. Ne pas lancer la page en `file://`, car elle charge les
JSON avec `fetch`.

## GitHub Pages

Le contenu du dossier peut être envoyé directement à la racine du dépôt :

```bash
git add .
git commit -m "Carnet Peche JP V6 Travel Loadout"
git push
```

Aucune étape de build n'est nécessaire. Le service worker V6 utilise un nouveau cache afin
de forcer la prise en compte de l'interface après déploiement.

`.gitignore` est optionnel pour le fonctionnement du site : si le sélecteur de fichiers du
navigateur le masque, il peut être ignoré ou créé directement dans GitHub.

## `synthesis.json`

Les grands paragraphes historiques de synthèse sont conservés comme couche narrative, mais
la **couche technique V5** (`technique_v5`), complétée par les règles loadout V6 a été ajoutée séparément : grammaire des animations,
logique couleur, rôles de leurres par espèce et sources techniques. Elle est celle utilisée par
les nouveaux onglets Leurres / Couleur / Animation.


## Sources matériel V6

Les plages de lancer cannes sont vérifiées sur les fiches Ultimate Fishing : SP82M Quattro 8–30 g et SP82MH Quattro 12–45 g. Le rôle des moulinets est recoupé avec les pages Shimano Twin Power XD (faible inertie / contrôle technique) et Twin Power FE (CoreSolid / rigidité sous charge). Les URLs et la distinction entre données fabricant et plafond utilisateur 50 g sont conservées dans `research/travel_loadout_v6_sources.json`.
