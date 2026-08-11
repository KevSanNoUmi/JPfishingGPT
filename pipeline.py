"""
Pipeline base de connaissance pêche Japon — v5.
Usage :
    export ANTHROPIC_API_KEY=sk-ant-...
    python pipeline.py init                                # crée/migre la base (schema.sql)
    python pipeline.py add-source                           # ajoute une source
    python pipeline.py extract <source_id> <fichier.txt>    # extraction multi-espèces (texte JP brut accepté)
    python pipeline.py review                                # observations à valider
    python pipeline.py validate <observation_id>              # valide une observation
    python pipeline.py add-lure                                # leurre (top 10 par espèce)
    python pipeline.py add-combo                                # combo canne
    python pipeline.py link-combo <lure_id> <combo_id>
    python pipeline.py add-stop                                  # étape du voyage (+ port de marée)
    python pipeline.py brief                                      # génère les briefs de session (API Claude)
    python pipeline.py import-log <sessions.json>                  # importe un log terrain exporté depuis la PWA
    python pipeline.py bootstrap-json data.json --force              # reconstruit la DB depuis un export JSON
    python pipeline.py import-research research/fichier.json         # deep-research -> obs + intel + marées
    python pipeline.py brief-local                                   # brief déterministe depuis l'intel locale
    python pipeline.py export                                       # génère data.json + tides_2026.json
"""

import sqlite3
import json
import sys
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "peche_jp.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
LURE_TYPO_PATH = os.path.join(os.path.dirname(__file__), "lure_typology.json")
MAX_LURE_WEIGHT_G = 50.0  # plafond utilisateur : aucune recommandation > 50 g
TIDES_PATH = os.path.join(os.path.dirname(__file__), "tides_2026.json")

SEARCH_DIMS = {
    "saison", "maree", "moment_jour", "spot_type", "leurre", "comportement",
    "profondeur", "temperature_eau", "couleur_eau", "pression_atmo", "observation", "zone",
}
DERIVED_RESEARCH_TYPES = {"synthesis", "lure_box_synthesis", "trip_plan_seed", "decision_engine", "trip_plan", "trip_tool", "research_method"}
EVIDENCE_CONFIDENCE = {4: 0.85, 3: 0.70, 2: 0.55, 1: 0.40}
JST = timezone(timedelta(hours=9))

# Vocabulaire contrôlé — DOIT rester identique aux options du QCM côté app
VOCAB = {
    "maree": ["montante", "descendante", "étale"],
    "moment_jour": ["aube", "jour", "crépuscule", "nuit"],
    "couleur_eau": ["claire", "trouble", "verte"],
    "pression_atmo": ["basse", "moyenne", "haute"],
}

EXTRACTION_PROMPT = """Tu extrais des observations de pêche factuelles depuis un texte japonais (brut, non traduit — tu lis le japonais directement) ou une transcription vidéo. Contexte : pêche du bord au Japon, période novembre / 10 premiers jours de décembre.

Espèces reconnues (utilise EXACTEMENT ces noms dans le champ "species") :
hirame (ヒラメ), suzuki (スズキ/シーバス), hamachi (ハマチ/ブリ/イナダ/ワラサ), aori-ika (アオリイカ), kurodai (クロダイ/チヌ), madai (マダイ), tachiuo (タチウオ), saba (サバ), aji (アジ), mebaru (メバル)

Règles strictes :
- Une observation = un fait vérifiable et actionnable, rattaché à UNE espèce
- Un même texte peut produire des observations pour plusieurs espèces différentes
- Paraphrase fidèle en français, jamais de citation mot pour mot du texte source
- N'invente rien : si l'info n'est pas dans le texte, ne crée ni observation ni champ de recommandation
- Ignore ce qui ne concerne pas la pêche du bord ou une espèce de la liste
- Comportement général toute saison → tag "saison": "general"
- Si le texte donne une recommandation concrète (leurre, couleur, animation, bas de ligne) pour des conditions données, remplis les champs recommended_*. Sinon omets-les.
- Conserve les termes techniques japonais intraduisibles entre parenthèses dans la paraphrase (ex: "courant de retour (離岸流)", "veine de courant (ヨレ)", "rupture de fond (ブレイク)")

Vocabulaire contrôlé OBLIGATOIRE pour ces 4 dimensions (le QCM de l'app matche dessus) :
- maree : uniquement "montante", "descendante" ou "étale"
- moment_jour : uniquement "aube", "jour", "crépuscule" ou "nuit"
- couleur_eau : uniquement "claire", "trouble" ou "verte"
- pression_atmo : uniquement "basse", "moyenne" ou "haute"
Si le texte dit "marée haute" ou "満潮", interprète selon le contexte (montée → "montante", renverse → "étale"). Si ambigu, omets le tag plutôt que d'inventer.

Sortie JSON stricte, un array d'objets, RIEN d'autre (pas de préambule, pas de ```json) :
[
  {{
    "species": "hirame",
    "raw_text": "paraphrase courte et factuelle",
    "recommended_lure": "…",
    "recommended_color": "…",
    "recommended_animation": "…",
    "recommended_leader": "…",
    "tags": {{
      "saison": "…", "maree": "…", "moment_jour": "…", "spot_type": "…",
      "leurre": "…", "comportement": "…", "profondeur": "…",
      "temperature_eau": "…", "couleur_eau": "…", "pression_atmo": "…"
    }}
  }}
]

Ne remplis que les clés pour lesquelles le texte donne une info explicite. Omets les autres (pas de null).

Texte source :
{texte}
"""

BRIEF_PROMPT = """Tu es un guide de pêche technique. Rédige un briefing de session concis (8-12 lignes max) pour cette étape, en te basant EXCLUSIVEMENT sur les observations fournies ci-dessous. Chaque affirmation doit citer ses observations sources entre crochets [#id].

Règles :
- N'affirme RIEN qui ne soit pas dans les observations. S'il manque une info (ex: aucune donnée marée pour une espèce), dis-le explicitement.
- Structure : par espèce ciblée. Pour chaque espèce : fenêtre horaire/marée, type de spot à chercher, leurre + animation + couleur si disponibles, bas de ligne si disponible.
- Ton direct, technique, pas de remplissage. Français, termes japonais techniques conservés.
- Si deux observations divergent, mentionne les deux options avec leurs sources.

Étape : {city} ({dates})
Espèces ciblées : {species}

Observations validées disponibles :
{observations}
"""


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columns(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _ensure_column(conn, table, definition):
    name = definition.split()[0]
    if name not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def migrate_db(conn):
    """Migration additive v3 -> v5, sans destruction des données existantes."""
    _ensure_column(conn, "sources", "source_kind TEXT")
    _ensure_column(conn, "observations", "evidence_level INTEGER")
    _ensure_column(conn, "observations", "metadata_json TEXT")
    _ensure_column(conn, "observations", "typology_json TEXT")
    _ensure_column(conn, "observations", "fingerprint TEXT")
    _ensure_column(conn, "trip_stops", "arrival_date TEXT")
    _ensure_column(conn, "trip_stops", "stay_dates_json TEXT")
    _ensure_column(conn, "trip_stops", "summary_json TEXT")
    _ensure_column(conn, "combos", "setup_json TEXT")
    conn.executescript("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_observation_fingerprint
          ON observations(fingerprint) WHERE fingerprint IS NOT NULL;
        CREATE TABLE IF NOT EXISTS trip_intel (
            id INTEGER PRIMARY KEY,
            stop_id INTEGER NOT NULL REFERENCES trip_stops(id),
            category TEXT NOT NULL,
            text TEXT NOT NULL,
            source_label TEXT,
            source_url TEXT,
            confidence_level INTEGER,
            metadata_json TEXT,
            fingerprint TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS tide_days (
            id INTEGER PRIMARY KEY,
            port TEXT NOT NULL,
            date TEXT NOT NULL,
            station_label TEXT,
            station_code TEXT,
            source_url TEXT,
            proxy_note TEXT,
            high_tides_json TEXT NOT NULL,
            low_tides_json TEXT NOT NULL,
            UNIQUE(port, date)
        );
        INSERT OR IGNORE INTO tag_dimensions (name) VALUES ('observation'), ('zone');
    """)


def init_db():
    conn = get_conn()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    migrate_db(conn)
    conn.commit()
    conn.close()
    print(f"Base v5 initialisée/migrée : {DB_PATH}")


def normalize_species_key(value):
    s = (value or "").strip().lower().replace("_", "-")
    s = re.sub(r"\s+", "-", s)
    return s


def species_map(conn):
    """Alias normalisé -> id (accepte aori_ika / aori-ika, etc.)."""
    m = {}
    for sid, name_fr, aliases in conn.execute("SELECT id, name_fr, aliases FROM species"):
        for raw in [name_fr] + (aliases or "").split(","):
            key = normalize_species_key(raw)
            if key:
                m[key] = sid
    return m


def add_source():
    print("Type de source : marque / blog / video / terrain")
    type_ = input("type: ").strip()
    weight_map = {"marque": 1.0, "blog": 0.7, "video": 0.7, "terrain": 1.0}
    weight = weight_map.get(type_, 0.4)
    label = input("label (nom du site/chaîne/auteur): ").strip()
    url = input("url (optionnel): ").strip() or None
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO sources (url, type, label, weight) VALUES (?, ?, ?, ?)",
        (url, type_, label, weight),
    )
    conn.commit()
    print(f"Source créée, id = {cur.lastrowid}, poids = {weight}")
    conn.close()


def add_lure():
    conn = get_conn()
    smap = {r[1]: r[0] for r in conn.execute("SELECT id, name_fr FROM species")}
    print("Espèces :", ", ".join(f"{v}={k}" for k, v in smap.items()))
    sp_id = int(input("id espèce: ").strip())
    name = input("nom du leurre: ").strip()
    type_ = input("type (jerkbait/vibration/popper/jig/metal/egi...): ").strip()
    rank = input("rang dans le top 10 (1 = priorité max): ").strip()
    cur = conn.execute(
        "INSERT INTO lures (species_id, name, type, rank) VALUES (?, ?, ?, ?)",
        (sp_id, name, type_, int(rank) if rank else 99),
    )
    conn.commit()
    print(f"Leurre créé, id = {cur.lastrowid}")
    n = conn.execute("SELECT COUNT(*) FROM lures WHERE species_id = ?", (sp_id,)).fetchone()[0]
    if n > 10:
        print(f"⚠️  {n} leurres pour cette espèce — dépasse le max de 10.")
    conn.close()


def add_combo():
    conn = get_conn()
    name = input("nom du combo (ex: SP82MH): ").strip()
    desc = input("description (ex: gros hirame / grosses conditions): ").strip()
    cur = conn.execute("INSERT INTO combos (name, description) VALUES (?, ?)", (name, desc))
    conn.commit()
    print(f"Combo créé, id = {cur.lastrowid}")
    conn.close()


def add_stop():
    conn = get_conn()
    city = input("ville / spot (ex: Numazu / Izu): ").strip()
    dates = input("dates (ex: 29-30 nov): ").strip()
    arrival_date = input("date d'arrivée YYYY-MM-DD (optionnel): ").strip() or None
    stay_raw = input("jours exacts de pêche YYYY-MM-DD, séparés par virgules (max 4, optionnel): ").strip()
    stay_dates = [x.strip() for x in stay_raw.split(",") if x.strip()][:4]
    if not stay_dates and arrival_date:
        stay_dates = [arrival_date]
    species = input("espèces ciblées, séparées par des virgules: ").strip()
    port = input("clé marée (shimizu/fukuoka/itoshima/kobe/toba/numazu/tokyo/kashima, vide si aucun): ").strip() or None
    cur = conn.execute(
        "INSERT INTO trip_stops (city, dates, arrival_date, stay_dates_json, target_species, port) VALUES (?, ?, ?, ?, ?, ?)",
        (city, dates, arrival_date, json.dumps(stay_dates, ensure_ascii=False) if stay_dates else None, species, port),
    )
    conn.commit()
    print(f"Étape créée, id = {cur.lastrowid}")
    conn.close()


def link_combo(lure_id, combo_id):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO lure_combo (lure_id, combo_id) VALUES (?, ?)", (lure_id, combo_id))
    conn.commit()
    conn.close()
    print(f"Leurre {lure_id} rattaché au combo {combo_id}")


def _scalar_text(value):
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return None
    if isinstance(value, bool):
        return "oui" if value else "non"
    return str(value).strip()


def iter_search_tags(tags):
    """Explose les listes en tags multiples; ignore les objets riches (gardés en metadata_json)."""
    for dim, value in (tags or {}).items():
        if dim not in SEARCH_DIMS or value in (None, "", [], {}):
            continue
        values = value if isinstance(value, (list, tuple, set)) else [value]
        for item in values:
            txt = _scalar_text(item)
            if txt:
                yield dim, txt


def get_or_create_tag(conn, dimension, value):
    dim_row = conn.execute("SELECT id FROM tag_dimensions WHERE name = ?", (dimension,)).fetchone()
    if not dim_row:
        raise ValueError(f"Dimension inconnue : {dimension}")
    dim_id = dim_row[0]
    txt = _scalar_text(value)
    if not txt:
        raise ValueError(f"Valeur non scalaire pour {dimension}")
    txt = txt.lower()
    if dimension in VOCAB and txt not in VOCAB[dimension]:
        raise ValueError(f"Valeur '{txt}' hors vocabulaire pour {dimension} (attendu: {VOCAB[dimension]})")
    row = conn.execute("SELECT id FROM tags WHERE dimension_id = ? AND value = ?", (dim_id, txt)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO tags (dimension_id, value) VALUES (?, ?)", (dim_id, txt))
    return cur.lastrowid


def call_claude(prompt, max_tokens=4000):
    try:
        import anthropic
    except ImportError:
        sys.exit("Installe le SDK : pip install anthropic --break-system-packages")
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def parse_json_response(raw):
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[4:] if raw.startswith("json") else raw
    return json.loads(raw)


def compute_confidence(conn, species_id, source_id, source_weight, tags):
    """Concordance : une source distincte confirme si >=2 tags structurés sont partagés."""
    pairs = list(iter_search_tags(tags))
    if len(pairs) < 2:
        return min(float(source_weight), 1.0)

    tag_conditions, params = [], []
    for dim, val in pairs:
        if dim in VOCAB and val.lower() not in VOCAB[dim]:
            continue
        tag_conditions.append("(td.name = ? AND t.value = ?)")
        params.extend([dim, val.lower()])
    if len(tag_conditions) < 2:
        return min(float(source_weight), 1.0)

    query = f"""
        SELECT o.source_id, COUNT(*) as shared
        FROM observations o
        JOIN observation_tags ot ON ot.observation_id = o.id
        JOIN tags t ON t.id = ot.tag_id
        JOIN tag_dimensions td ON td.id = t.dimension_id
        WHERE o.species_id = ? AND o.source_id != ?
          AND ({" OR ".join(tag_conditions)})
        GROUP BY o.id
        HAVING shared >= 2
    """
    rows = conn.execute(query, [species_id, source_id] + params).fetchall()
    concordant_sources = len({r[0] for r in rows})
    bonus = min(0.15 * concordant_sources, 0.45)
    return min(float(source_weight) + bonus, 1.0)


def make_fingerprint(*parts):
    payload = "\x1f".join(str(p or "").strip().lower() for p in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def insert_observation(conn, species_id, source_id, source_weight, obs):
    tags = obs.get("tags") or {}
    override = obs.get("_confidence_override")
    score = float(override) if override is not None else compute_confidence(conn, species_id, source_id, source_weight, tags)
    evidence_level = obs.get("evidence_level")
    needs_review = int(obs.get("_needs_review", 1 if score < 0.5 else 0))
    metadata = obs.get("metadata")
    fp = obs.get("fingerprint")
    cur = conn.execute(
        """INSERT INTO observations
           (species_id, source_id, raw_text, confidence_score, evidence_level, needs_review,
            recommended_lure, recommended_color, recommended_animation, recommended_leader,
            metadata_json, typology_json, fingerprint)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (species_id, source_id, obs["raw_text"], score, evidence_level, needs_review,
         obs.get("recommended_lure") or None, obs.get("recommended_color") or None,
         obs.get("recommended_animation") or None, obs.get("recommended_leader") or None,
         json.dumps(metadata, ensure_ascii=False) if metadata else None,
         json.dumps(obs.get("typology"), ensure_ascii=False) if obs.get("typology") else None, fp),
    )
    obs_id = cur.lastrowid
    skipped = []
    for dim, val in iter_search_tags(tags):
        try:
            tag_id = get_or_create_tag(conn, dim, val)
        except ValueError as e:
            skipped.append(str(e))
            continue
        conn.execute("INSERT OR IGNORE INTO observation_tags (observation_id, tag_id) VALUES (?, ?)", (obs_id, tag_id))
    return obs_id, score, needs_review, skipped


def extract(source_id, filepath):
    with open(filepath, encoding="utf-8") as f:
        texte = f.read()

    conn = get_conn()
    src = conn.execute("SELECT weight FROM sources WHERE id = ?", (source_id,)).fetchone()
    if not src:
        sys.exit(f"Source id {source_id} introuvable. Lance 'add-source' d'abord.")
    source_weight = src[0]
    smap = species_map(conn)

    observations = parse_json_response(call_claude(EXTRACTION_PROMPT.format(texte=texte)))
    print(f"{len(observations)} observation(s) extraite(s).")

    for obs in observations:
        sp_key = (obs.get("species") or "").strip().lower()
        species_id = smap.get(sp_key)
        if not species_id:
            print(f"  [IGNORÉ] espèce inconnue '{sp_key}' — {obs.get('raw_text','')[:60]}")
            continue
        obs_id, score, needs_review, skipped = insert_observation(conn, species_id, source_id, source_weight, obs)
        flag = "⚠️ À VÉRIFIER" if needs_review else "✓"
        reco = " [reco]" if obs.get("recommended_lure") else ""
        print(f"  [{flag}]{reco} #{obs_id} {sp_key} score={score:.2f} — {obs['raw_text'][:60]}")
        for s in skipped:
            print(f"      tag ignoré: {s}")

    conn.commit()
    conn.close()


def import_log(filepath):
    """Importe le log PWA. Les listes du QCM (lecture du spot) sont désormais supportées."""
    with open(filepath, encoding="utf-8") as f:
        sessions = json.load(f)

    conn = get_conn(); migrate_db(conn)
    smap = species_map(conn)
    src = conn.execute("SELECT id FROM sources WHERE type='terrain' AND label='Sessions terrain (PWA)'").fetchone()
    if src:
        source_id = src[0]
    else:
        cur = conn.execute(
            "INSERT INTO sources (url, type, source_kind, label, weight) VALUES (NULL, 'terrain', 'pwa_session', 'Sessions terrain (PWA)', 1.0)")
        source_id = cur.lastrowid

    imported = 0
    for sess in sessions:
        sp_key = normalize_species_key(sess.get("species"))
        species_id = smap.get(sp_key)
        if not species_id:
            print(f"  [IGNORÉ] espèce inconnue '{sp_key}'")
            continue
        result = sess.get("result", "rien")
        lure = (sess.get("lure") or "").strip()
        cast_weight = sess.get("cast_weight_g")
        try: cast_weight = float(cast_weight) if cast_weight not in (None, "") else None
        except (TypeError, ValueError): cast_weight = None
        conds = dict(sess.get("conditions") or {})
        # observation peut être un array : iter_search_tags l'explose proprement.
        date_txt = sess.get("date", "?")
        combo = (sess.get("combo") or "").strip() or None
        gear_txt = f" · combo {combo}" if combo else ""
        weight_txt = f" · {cast_weight:g} g total" if cast_weight is not None else ""
        if result == "rien":
            txt = f"Session sans touche ({date_txt}) au {lure}{weight_txt}{gear_txt} — conditions notées, à recouper"
        else:
            txt = f"Prise confirmée ({result}, {date_txt}) au {lure}{weight_txt}{gear_txt}"
            if sess.get("notes"):
                txt += f" — {sess['notes']}"
        fp = make_fingerprint("pwa", species_id, date_txt, lure, cast_weight, combo, result, sess.get("notes"), json.dumps(conds, ensure_ascii=False, sort_keys=True))
        if conn.execute("SELECT id FROM observations WHERE fingerprint=?", (fp,)).fetchone():
            print(f"  [DOUBLON] {date_txt} {sp_key} {lure}")
            continue
        obs = {
            "raw_text": txt,
            "recommended_lure": lure if result != "rien" and (cast_weight is None or cast_weight <= MAX_LURE_WEIGHT_G) else None,
            "tags": conds,
            "metadata": {"pwa_session": sess},
            "evidence_level": 4,
            "fingerprint": fp,
            "_needs_review": 0,
        }
        obs_id, score, _, skipped = insert_observation(conn, species_id, source_id, 1.0, obs)
        imported += 1
        print(f"  ✓ #{obs_id} {sp_key} score={score:.2f} — {txt[:70]}")
        for item in skipped:
            print(f"      tag ignoré: {item}")

    conn.commit(); conn.close()
    print(f"{imported} session(s) importée(s) comme observations terrain.")


def _source_profile(source_kind, evidence_level=None):
    kind = (source_kind or "blog").strip()
    if kind in {"marque", "blog", "video", "terrain"}:
        return kind, {"marque":1.0,"blog":0.7,"video":0.7,"terrain":1.0}[kind]
    if "video" in kind:
        core = "video"
    else:
        core = "blog"
    if evidence_level in EVIDENCE_CONFIDENCE:
        weight = EVIDENCE_CONFIDENCE[evidence_level]
    elif kind.startswith("official"):
        weight = 0.90
    elif "catch" in kind or "field" in kind or "shop" in kind:
        weight = 0.80
    else:
        weight = 0.65
    return core, weight


def _get_or_create_source(conn, label, source_kind, url=None, evidence_level=None):
    row = conn.execute("SELECT id, weight FROM sources WHERE label = ?", (label,)).fetchone()
    if row:
        # complète les infos si elles manquaient dans une ancienne DB
        conn.execute("UPDATE sources SET source_kind=COALESCE(source_kind, ?), url=COALESCE(url, ?) WHERE id=?", (source_kind, url, row[0]))
        return row[0], row[1]
    core, weight = _source_profile(source_kind, evidence_level)
    cur = conn.execute(
        "INSERT INTO sources (url, type, source_kind, label, weight) VALUES (?, ?, ?, ?, ?)",
        (url, core, source_kind, label, weight),
    )
    return cur.lastrowid, weight


def import_extracted(filepath):
    """Importe des observations déjà extraites. Les métadonnées riches sont préservées."""
    with open(filepath, encoding="utf-8") as f:
        entries = json.load(f)
    conn = get_conn(); migrate_db(conn)
    smap = species_map(conn)
    imported, ignored = 0, 0
    for e in entries:
        label = (e.get("source_label") or "").strip()
        if not label:
            ignored += 1; continue
        sp_key = normalize_species_key(e.get("species"))
        species_id = smap.get(sp_key)
        if not species_id:
            print(f"  [IGNORÉ] espèce inconnue '{sp_key}' — {e.get('raw_text','')[:50]}")
            ignored += 1; continue
        level = int((e.get("tags") or {}).get("confidence_level") or e.get("evidence_level") or 0) or None
        kind = (e.get("source_type") or "blog").strip()
        url = e.get("source_url") or (e.get("tags") or {}).get("source_url")
        source_id, source_weight = _get_or_create_source(conn, label, kind, url, level)
        obs = dict(e)
        obs["metadata"] = e.get("metadata") or e.get("tags")
        if level:
            obs["evidence_level"] = level
        fp = make_fingerprint("extracted", sp_key, label, e.get("raw_text"), e.get("recommended_lure"))
        if conn.execute("SELECT id FROM observations WHERE fingerprint=?", (fp,)).fetchone():
            continue
        obs["fingerprint"] = fp
        obs_id, score, needs_review, skipped = insert_observation(conn, species_id, source_id, source_weight, obs)
        imported += 1
        flag = "⚠️ À VÉRIFIER" if needs_review else "✓"
        print(f"  [{flag}] #{obs_id} {sp_key} score={score:.2f} ({label}) — {e['raw_text'][:60]}")
        for item in skipped:
            print(f"      tag ignoré: {item}")
    conn.commit(); conn.close()
    print(f"\n{imported} observation(s) importée(s), {ignored} ignorée(s).")



def _infer_moment(tags):
    raw = str((tags or {}).get("moment_jour") or "").lower()
    mapping = {"dawn":"aube","predawn":"aube","aube":"aube","day":"jour","daytime":"jour","jour":"jour","evening":"crépuscule","dusk":"crépuscule","crépuscule":"crépuscule","night":"nuit","nuit":"nuit"}
    if raw in mapping:
        return mapping[raw]
    # cherche une heure explicite dans les métadonnées
    for key in ("time", "time_evening_capture", "time_bites_start", "recent_capture_reference", "moment_jour"):
        val = (tags or {}).get(key)
        m = re.search(r"\b(\d{1,2}):(\d{2})\b", str(val or ""))
        if not m:
            continue
        h = int(m.group(1)) + int(m.group(2))/60
        if 4.5 <= h <= 7.5: return "aube"
        if 16 <= h < 18: return "crépuscule"
        if h >= 18 or h < 4.5: return "nuit"
        return "jour"
    return None


def _research_tags(entry):
    meta = entry.get("tags") or {}
    out = {}
    moment = _infer_moment(meta)
    if moment: out["moment_jour"] = moment
    if meta.get("zone"): out["zone"] = meta["zone"]
    structure = meta.get("structure") or meta.get("bottom")
    if structure: out["spot_type"] = structure
    behavior = meta.get("biological_signs") or meta.get("moment_touche") or meta.get("morning_pattern")
    if behavior: out["comportement"] = behavior
    if entry.get("recommended_lure"): out["leurre"] = entry["recommended_lure"]
    date = str(meta.get("date") or meta.get("date_published") or "")
    if "-11-" in date: out["saison"] = "novembre"
    elif "-12-" in date: out["saison"] = "décembre"
    # uniquement si une vraie phase contrôlée est déjà fournie
    phase = str(meta.get("maree") or "").lower()
    if phase in VOCAB["maree"]: out["maree"] = phase
    return out


def _research_stop_ids(filepath):
    name = os.path.basename(filepath).lower()
    if "fukuoka" in name: return [2, 3]
    if "kobe" in name: return [4]
    if "ise_shima" in name or "ise-shima" in name: return [5]
    if "numazu" in name: return [6]
    if "shizuoka" in name: return [1]
    if "tokyo" in name: return [7]
    if "kashima" in name: return [8]
    return []


def _intel_category(source_kind):
    k = (source_kind or "").lower()
    if "regulation" in k or "access" in k or "safety" in k or "official_local" in k:
        return "access"
    if "tide" in k or "astronomical" in k or "environment" in k:
        return "conditions"
    if k in DERIVED_RESEARCH_TYPES or "plan" in k or "decision" in k:
        return "strategy"
    if "catch" in k or "field" in k or "shop" in k:
        return "field"
    return "context"


def _infer_tide_port(filepath, entry):
    tags = entry.get("tags") or {}
    if tags.get("port_key"):
        return tags["port_key"]
    name = os.path.basename(filepath).lower()
    if "fukuoka" in name: return "fukuoka"
    if "kobe" in name: return "kobe"
    if "numazu" in name: return "numazu"
    return None


def _upsert_tide_entry(conn, filepath, entry):
    if entry.get("source_type") != "official_tide_forecast":
        return False
    tags = entry.get("tags") or {}
    if not tags.get("date") or not tags.get("high_tides") and not tags.get("low_tides"):
        return False
    port = _infer_tide_port(filepath, entry)
    if not port: return False
    url = entry.get("source_url") or tags.get("source_url")
    conn.execute("""INSERT INTO tide_days
        (port,date,station_label,station_code,source_url,proxy_note,high_tides_json,low_tides_json)
        VALUES (?,?,?,?,?,?,?,?)
        ON CONFLICT(port,date) DO UPDATE SET
          station_label=excluded.station_label, station_code=excluded.station_code,
          source_url=COALESCE(excluded.source_url,tide_days.source_url), proxy_note=excluded.proxy_note,
          high_tides_json=excluded.high_tides_json, low_tides_json=excluded.low_tides_json""",
        (port, tags["date"], tags.get("station") or tags.get("location") or entry.get("source_label"),
         tags.get("station_code"), url, tags.get("proxy_note"),
         json.dumps(tags.get("high_tides") or [], ensure_ascii=False), json.dumps(tags.get("low_tides") or [], ensure_ascii=False)))
    # Hakata sert explicitement de référence de phase pour l'étape Itoshima dans le deep research.
    if port == "fukuoka":
        conn.execute("""INSERT INTO tide_days
            (port,date,station_label,station_code,source_url,proxy_note,high_tides_json,low_tides_json)
            VALUES ('itoshima',?,?,?,?,?,?,?)
            ON CONFLICT(port,date) DO UPDATE SET station_label=excluded.station_label, station_code=excluded.station_code,
              source_url=excluded.source_url, proxy_note=excluded.proxy_note,
              high_tides_json=excluded.high_tides_json, low_tides_json=excluded.low_tides_json""",
            (tags["date"], tags.get("station") or tags.get("location") or "Hakata", tags.get("station_code") or "QF", url,
             "Hakata JMA utilisé comme référence de phase pour Itoshima; vérifier le décalage local.",
             json.dumps(tags.get("high_tides") or [], ensure_ascii=False), json.dumps(tags.get("low_tides") or [], ensure_ascii=False)))
    return True


def import_research(filepath):
    """Deep research -> observations directes + intel voyage + marées officielles, idempotent."""
    with open(filepath, encoding="utf-8") as f:
        entries = json.load(f)
    conn = get_conn(); migrate_db(conn)
    smap = species_map(conn)
    stop_ids = _research_stop_ids(filepath)
    n_obs = n_intel = n_tide = n_skip = 0
    for e in entries:
        kind = (e.get("source_type") or "research").strip()
        meta = e.get("tags") or {}
        level = int(meta.get("confidence_level") or 0) or None
        url = e.get("source_url") or meta.get("source_url")
        if _upsert_tide_entry(conn, filepath, e):
            n_tide += 1
        sp_key = normalize_species_key(e.get("species"))
        species_id = smap.get(sp_key)
        derived = kind in DERIVED_RESEARCH_TYPES
        if species_id and not derived:
            label = (e.get("source_label") or kind).strip()
            source_id, source_weight = _get_or_create_source(conn, label, kind, url, level)
            fp = make_fingerprint("research", sp_key, label, e.get("raw_text"), meta.get("date"), meta.get("time"), e.get("recommended_lure"))
            if not conn.execute("SELECT id FROM observations WHERE fingerprint=?", (fp,)).fetchone():
                obs = {
                    "raw_text": e.get("raw_text") or "",
                    "recommended_lure": e.get("recommended_lure"),
                    "recommended_color": e.get("recommended_color"),
                    "recommended_animation": e.get("recommended_animation"),
                    "recommended_leader": e.get("recommended_leader"),
                    "tags": _research_tags(e),
                    "metadata": meta,
                    "evidence_level": level,
                    "fingerprint": fp,
                    "_confidence_override": EVIDENCE_CONFIDENCE.get(level, source_weight),
                    "_needs_review": 1 if (level or 0) < 2 else 0,
                }
                insert_observation(conn, species_id, source_id, source_weight, obs)
                n_obs += 1
        elif sp_key not in {"general", ""} and not species_id:
            n_skip += 1

        # Toute information générale, réglementaire ou synthétique nourrit l'intel du séjour,
        # sans être comptée comme source indépendante dans la concordance espèces.
        if stop_ids and (sp_key == "general" or derived):
            for stop_id in stop_ids:
                fp = make_fingerprint("intel", stop_id, e.get("source_label"), e.get("raw_text"))
                try:
                    conn.execute("""INSERT INTO trip_intel
                        (stop_id,category,text,source_label,source_url,confidence_level,metadata_json,fingerprint)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (stop_id, _intel_category(kind), e.get("raw_text") or "", e.get("source_label"), url, level,
                         json.dumps(meta, ensure_ascii=False) if meta else None, fp))
                    n_intel += 1
                except sqlite3.IntegrityError:
                    pass
    conn.commit(); conn.close()
    print(f"Research importé: {n_obs} obs directes, {n_intel} intel, {n_tide} jour(s) de marée, {n_skip} espèces hors cible ignorées.")


def bootstrap_json(filepath, force=False):
    """Reconstruit une DB v5 à partir d'un data.json existant, utile quand le .db n'était pas versionné."""
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(DB_PATH):
        conn = get_conn()
        try: count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        except sqlite3.Error: count = 0
        conn.close()
        if count:
            sys.exit("La base contient déjà des observations. Utilise --force pour la reconstruire.")
    init_db()
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    conn = get_conn(); migrate_db(conn)
    source_cache = {}
    for o in data.get("observations", []):
        label = o.get("source") or "Source importée"
        kind = o.get("source_type") or "blog"
        key=(label,kind)
        if key not in source_cache:
            source_cache[key] = _get_or_create_source(conn, label, kind, (o.get("metadata") or {}).get("source_url"))[0]
        source_id=source_cache[key]
        rec=o.get("recommendation") or {}
        conn.execute("""INSERT OR REPLACE INTO observations
            (id,species_id,source_id,raw_text,confidence_score,evidence_level,needs_review,
             recommended_lure,recommended_color,recommended_animation,recommended_leader,metadata_json,typology_json,fingerprint)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (o["id"],o["species_id"],source_id,o.get("text") or "",float(o.get("confidence") or 0),o.get("evidence_level"),0,
             rec.get("lure"),rec.get("color"),rec.get("animation"),rec.get("leader"),
             json.dumps(o.get("metadata"),ensure_ascii=False) if o.get("metadata") else None,
             json.dumps(rec.get("typology"),ensure_ascii=False) if rec.get("typology") else None,
             make_fingerprint("legacy",o["id"],o.get("species"),o.get("text"))))
        for dim,val in iter_search_tags(o.get("tags") or {}):
            try: tag_id=get_or_create_tag(conn,dim,val)
            except ValueError: continue
            conn.execute("INSERT OR IGNORE INTO observation_tags (observation_id,tag_id) VALUES (?,?)",(o["id"],tag_id))
    for c in data.get("combos", []):
        conn.execute("INSERT OR REPLACE INTO combos (id,name,description,setup_json) VALUES (?,?,?,?)",
                     (c["id"],c["name"],c.get("description"),
                      json.dumps(c.get("setup"),ensure_ascii=False) if c.get("setup") else None))
    for l in data.get("lures", []):
        conn.execute("INSERT OR REPLACE INTO lures (id,species_id,name,type,rank) VALUES (?,?,?,?,?)",(l["id"],l["species_id"],l["name"],l.get("type"),l.get("rank",99)))
        for combo_name in l.get("combos",[]):
            row=conn.execute("SELECT id FROM combos WHERE name=?",(combo_name,)).fetchone()
            if row: conn.execute("INSERT OR IGNORE INTO lure_combo (lure_id,combo_id) VALUES (?,?)",(l["id"],row[0]))
    for st in data.get("trip_stops", []):
        targets=st.get("target_species") or []
        if isinstance(targets,list): targets=",".join(targets)
        conn.execute("""INSERT OR REPLACE INTO trip_stops
            (id,city,dates,arrival_date,stay_dates_json,summary_json,target_species,port)
            VALUES (?,?,?,?,?,?,?,?)""",
            (st["id"],st["city"],st["dates"],st.get("arrival_date"),
             json.dumps(st.get("stay_dates") or [],ensure_ascii=False) if st.get("stay_dates") else None,
             json.dumps(st.get("summary"),ensure_ascii=False) if st.get("summary") else None,
             targets,st.get("port")))
        if st.get("brief"):
            conn.execute("INSERT OR REPLACE INTO trip_briefs (stop_id,text) VALUES (?,?)",(st["id"],st["brief"]))
    conn.commit(); conn.close()
    print(f"DB reconstruite depuis {filepath}: {len(data.get('observations',[]))} observations.")


def brief_local():
    """Génère sans API un brief de voyage depuis les entrées strategy/access les mieux sourcées."""
    conn=get_conn(); migrate_db(conn)
    for stop in conn.execute("SELECT id,city FROM trip_stops ORDER BY id").fetchall():
        rows=conn.execute("""SELECT category,text,confidence_level FROM trip_intel
            WHERE stop_id=? ORDER BY CASE category WHEN 'strategy' THEN 0 WHEN 'access' THEN 1 WHEN 'field' THEN 2 ELSE 3 END,
            confidence_level DESC, id LIMIT 10""",(stop[0],)).fetchall()
        if not rows: continue
        lines=[f"# {stop[1]} — intel V5"]
        for cat,text,level in rows[:8]:
            lines.append(f"- {text} [intel {level or '?'}]")
        conn.execute("INSERT INTO trip_briefs (stop_id,text) VALUES (?,?) ON CONFLICT(stop_id) DO UPDATE SET text=excluded.text, generated_at=datetime('now')",(stop[0],"\n".join(lines)))
    conn.commit(); conn.close(); print("Briefs locaux régénérés depuis l'intel.")


def _normalize_lure_name(s):
    s=(s or "").lower()
    s=re.sub(r"[^a-z0-9à-ÿ]+"," ",s)
    return " ".join(s.split())


def _load_typology():
    if not os.path.exists(LURE_TYPO_PATH): return {}
    with open(LURE_TYPO_PATH,encoding="utf-8") as f: return json.load(f)


def _match_typology(lure, typo):
    q=_normalize_lure_name(lure)
    if len(q)<4: return None
    best=None; best_len=0
    for key,val in typo.items():
        for cand in (key, val.get("modele")):
            n=_normalize_lure_name(cand)
            if len(n)>=4 and (n in q or q in n) and len(n)>best_len:
                best=val; best_len=len(n)
    return best


def export_tides_json(conn=None):
    own = conn is None
    if own: conn=get_conn(); migrate_db(conn)
    ports={}
    for r in conn.execute("SELECT * FROM tide_days ORDER BY port,date"):
        port=r["port"] if isinstance(r,sqlite3.Row) else r[1]
        if not isinstance(r,sqlite3.Row):
            # get_conn sans row_factory
            cols=[x[1] for x in conn.execute("PRAGMA table_info(tide_days)")]; r=dict(zip(cols,r))
        ports.setdefault(port,{})[r["date"]]={
            "station":r["station_label"],"station_code":r["station_code"],"source_url":r["source_url"],
            "proxy_note":r["proxy_note"],"high_tides":json.loads(r["high_tides_json"]),"low_tides":json.loads(r["low_tides_json"]),
        }
    out={"updated":datetime.now(JST).date().isoformat(),"source_note":"Prévisions astronomiques JMA; ce ne sont pas des niveaux observés en temps réel.","ports":ports}
    with open(TIDES_PATH,"w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
    if own: conn.close()
    return out

def brief():
    """Génère un briefing de session par étape, à partir des observations validées."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    smap = species_map(conn)
    stops = conn.execute("SELECT * FROM trip_stops ORDER BY id").fetchall()
    if not stops:
        sys.exit("Aucune étape — lance add-stop d'abord.")

    for stop in stops:
        target = [x.strip() for x in (stop["target_species"] or "").split(",") if x.strip()]
        sp_ids = [smap.get(t.lower()) for t in target]
        sp_ids = [x for x in sp_ids if x]
        if not sp_ids:
            print(f"[{stop['city']}] aucune espèce reconnue, brief sauté.")
            continue

        placeholders = ",".join("?" * len(sp_ids))
        obs = conn.execute(
            f"""SELECT o.id, s.name_fr, o.raw_text, o.confidence_score,
                       o.recommended_lure, o.recommended_color, o.recommended_animation, o.recommended_leader,
                       src.label
                FROM observations o
                JOIN species s ON s.id = o.species_id
                JOIN sources src ON src.id = o.source_id
                WHERE o.needs_review = 0 AND o.species_id IN ({placeholders})
                ORDER BY o.species_id, o.confidence_score DESC""",
            sp_ids,
        ).fetchall()

        if not obs:
            print(f"[{stop['city']}] aucune observation validée pour {target}, brief sauté.")
            continue

        obs_txt = "\n".join(
            f"[#{o['id']}] ({o['name_fr']}, conf {o['confidence_score']:.2f}, src: {o['label']}) {o['raw_text']}"
            + (f" | reco: {o['recommended_lure'] or ''} {o['recommended_color'] or ''} {o['recommended_animation'] or ''} {o['recommended_leader'] or ''}".rstrip()
               if o['recommended_lure'] else "")
            for o in obs
        )
        text = call_claude(BRIEF_PROMPT.format(
            city=stop["city"], dates=stop["dates"], species=", ".join(target), observations=obs_txt
        ), max_tokens=1500)

        conn.execute(
            "INSERT INTO trip_briefs (stop_id, text) VALUES (?, ?) "
            "ON CONFLICT(stop_id) DO UPDATE SET text=excluded.text, generated_at=datetime('now')",
            (stop["id"], text),
        )
        conn.commit()
        print(f"[{stop['city']}] brief généré ({len(obs)} obs).")

    conn.close()


def review():
    conn = get_conn()
    rows = conn.execute(
        """SELECT o.id, s.name_fr, o.raw_text, o.confidence_score
           FROM observations o JOIN species s ON s.id = o.species_id
           WHERE o.needs_review = 1 ORDER BY o.confidence_score ASC"""
    ).fetchall()
    if not rows:
        print("Rien à vérifier.")
    for r in rows:
        print(f"[{r[0]}] {r[1]} score={r[3]:.2f} — {r[2]}")
    conn.close()


def validate(obs_id):
    conn = get_conn()
    conn.execute("UPDATE observations SET needs_review = 0 WHERE id = ?", (obs_id,))
    conn.commit()
    conn.close()
    print(f"Observation {obs_id} validée.")


def _recommendation_weight_g(reco, typology=None):
    """Poids lancé connu. Priorité à la typologie vérifiée, sinon poids explicite dans le nom de leurre."""
    tp = typology or (reco or {}).get("typology") or {}
    w = tp.get("poids") if isinstance(tp, dict) else None
    if isinstance(w, (int, float)):
        return float(w)
    lure = str((reco or {}).get("lure") or "")
    import re
    m = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*g\b", lure, flags=re.I)
    if m:
        try: return float(m.group(1).replace(",", "."))
        except ValueError: return None
    return None


def _recommendation_allowed(reco, typology=None):
    w = _recommendation_weight_g(reco, typology)
    return w is None or w <= MAX_LURE_WEIGHT_G


def export_json():
    conn = get_conn(); migrate_db(conn)
    conn.row_factory = sqlite3.Row
    typology = _load_typology()

    species_out = [dict(sp) for sp in conn.execute("SELECT id, name_jp, name_fr, name_latin FROM species")]
    obs_out = []
    for o in conn.execute(
        """SELECT o.*, s.name_fr as species, src.label as source_label,
                  COALESCE(src.source_kind,src.type) as source_type
           FROM observations o JOIN species s ON s.id=o.species_id
           JOIN sources src ON src.id=o.source_id
           WHERE o.needs_review=0 ORDER BY o.id""").fetchall():
        tag_rows=conn.execute("""SELECT td.name as dim,t.value FROM observation_tags ot
            JOIN tags t ON t.id=ot.tag_id JOIN tag_dimensions td ON td.id=t.dimension_id
            WHERE ot.observation_id=? ORDER BY td.name,t.value""",(o["id"],)).fetchall()
        tags={}
        for tr in tag_rows:
            dim,val=tr["dim"],tr["value"]
            if dim not in tags: tags[dim]=val
            elif not isinstance(tags[dim],list): tags[dim]=[tags[dim],val]
            else: tags[dim].append(val)
        entry={"id":o["id"],"species_id":o["species_id"],"species":o["species"],"text":o["raw_text"],
               "confidence":round(o["confidence_score"],2),"source":o["source_label"],"source_type":o["source_type"],"tags":tags}
        if o["evidence_level"] is not None: entry["evidence_level"]=o["evidence_level"]
        if o["metadata_json"]:
            try: entry["metadata"]=json.loads(o["metadata_json"])
            except json.JSONDecodeError: pass
        reco={f.replace("recommended_",""):o[f] for f in ("recommended_lure","recommended_color","recommended_animation","recommended_leader") if o[f]}
        if reco:
            tp=None
            if o["typology_json"]:
                try: tp=json.loads(o["typology_json"])
                except json.JSONDecodeError: tp=None
            if not tp: tp=_match_typology(reco.get("lure"),typology)
            weight_g=_recommendation_weight_g(reco,tp)
            # Une session terrain peut connaître le poids total lancé même si le nom du leurre ne l'encode pas.
            if weight_g is None:
                sess=((entry.get("metadata") or {}).get("pwa_session") or {})
                try:
                    sw=sess.get("cast_weight_g")
                    weight_g=float(sw) if sw not in (None, "") else None
                except (TypeError, ValueError):
                    weight_g=None
            if weight_g is None or weight_g <= MAX_LURE_WEIGHT_G:
                if tp: reco["typology"]=tp
                if weight_g is not None: reco["cast_weight_g"]=weight_g
                entry["recommendation"]=reco
            else:
                # On garde le fait biologique/terrain mais le leurre >50 g ne nourrit plus le moteur décisionnel.
                entry.setdefault("metadata",{})["gear_filter"]={"excluded_recommendation":True,"reason":"lure_over_50g","cast_weight_g":weight_g}
        obs_out.append(entry)

    lures_out=[]
    for l in conn.execute("SELECT * FROM lures ORDER BY species_id,rank"):
        combo_names=[r["name"] for r in conn.execute("SELECT c.name FROM lure_combo lc JOIN combos c ON c.id=lc.combo_id WHERE lc.lure_id=?",(l["id"],))]
        lures_out.append({"id":l["id"],"species_id":l["species_id"],"name":l["name"],"type":l["type"],"rank":l["rank"],"combos":combo_names})
    combos_out=[]
    for c in conn.execute("SELECT * FROM combos ORDER BY id"):
        item={"id":c["id"],"name":c["name"],"description":c["description"]}
        if c["setup_json"]:
            try: item["setup"]=json.loads(c["setup_json"])
            except json.JSONDecodeError: pass
        combos_out.append(item)
    briefs={b["stop_id"]:b["text"] for b in conn.execute("SELECT * FROM trip_briefs")}
    stops_out=[]
    for st in conn.execute("SELECT * FROM trip_stops ORDER BY id"):
        intel=[]
        for x in conn.execute("SELECT category,text,source_label,source_url,confidence_level,metadata_json FROM trip_intel WHERE stop_id=? ORDER BY confidence_level DESC,id",(st["id"],)):
            item={"category":x["category"],"text":x["text"],"source":x["source_label"],"confidence_level":x["confidence_level"]}
            if x["source_url"]: item["source_url"]=x["source_url"]
            if x["metadata_json"]:
                try: item["metadata"]=json.loads(x["metadata_json"])
                except json.JSONDecodeError: pass
            intel.append(item)
        stay_dates=[]; summary=None
        if st["stay_dates_json"]:
            try: stay_dates=json.loads(st["stay_dates_json"])
            except json.JSONDecodeError: stay_dates=[]
        if st["summary_json"]:
            try: summary=json.loads(st["summary_json"])
            except json.JSONDecodeError: summary=None
        stops_out.append({"id":st["id"],"city":st["city"],"dates":st["dates"],"port":st["port"],"arrival_date":st["arrival_date"],
                          "stay_dates":stay_dates,
                          "summary":summary,
                          "target_species":[x.strip() for x in (st["target_species"] or "").split(",") if x.strip()],
                          "brief":briefs.get(st["id"]),"intel":intel})
    result={"schema_version":6,"updated":datetime.now(JST).date().isoformat(),
            "gear_policy":{"max_lure_weight_g":MAX_LURE_WEIGHT_G,"rule":"Poids total lancé >50 g exclu des recommandations; 46–50 g = MH haute charge utilisateur."},
            "species":species_out,"observations":obs_out,
            "lures":lures_out,"combos":combos_out,"trip_stops":stops_out}
    out_path=os.path.join(os.path.dirname(__file__),"data.json")
    with open(out_path,"w",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2)
    export_tides_json(conn)
    conn.close()
    documented=len({o["species_id"] for o in obs_out})
    print(f"{len(obs_out)} obs / {documented} espèces documentées, {len(stops_out)} étapes → {out_path} + {TIDES_PATH}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd=sys.argv[1]
    dispatch={"init":init_db,"add-source":add_source,"add-lure":add_lure,"add-combo":add_combo,"add-stop":add_stop,
              "review":review,"brief":brief,"brief-local":brief_local,"export":export_json}
    if cmd in dispatch:
        dispatch[cmd]()
    elif cmd == "extract": extract(int(sys.argv[2]),sys.argv[3])
    elif cmd == "validate": validate(int(sys.argv[2]))
    elif cmd == "link-combo": link_combo(int(sys.argv[2]),int(sys.argv[3]))
    elif cmd == "import-log": import_log(sys.argv[2])
    elif cmd == "import-extracted": import_extracted(sys.argv[2])
    elif cmd == "import-research": import_research(sys.argv[2])
    elif cmd == "bootstrap-json": bootstrap_json(sys.argv[2], force="--force" in sys.argv[3:])
    else:
        print(__doc__)
