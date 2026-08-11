-- Schéma base de connaissance pêche Japon — v6.2
-- Multi-espèces, briefs, terrain PWA, intel locale et marées officielles 2026.

CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY,
    name_jp TEXT NOT NULL,
    name_fr TEXT NOT NULL,
    name_latin TEXT,
    aliases TEXT
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    url TEXT,
    type TEXT NOT NULL CHECK(type IN ('marque','blog','video','terrain')),
    source_kind TEXT,        -- type fin : catch_log, official_regulation, local_shop_field_intel...
    label TEXT NOT NULL,
    weight REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS tag_dimensions (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY,
    dimension_id INTEGER NOT NULL REFERENCES tag_dimensions(id),
    value TEXT NOT NULL,
    UNIQUE(dimension_id, value)
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY,
    species_id INTEGER NOT NULL REFERENCES species(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    raw_text TEXT NOT NULL,
    confidence_score REAL DEFAULT 0,
    evidence_level INTEGER,
    needs_review INTEGER DEFAULT 1,
    recommended_lure TEXT,
    recommended_color TEXT,
    recommended_animation TEXT,
    recommended_leader TEXT,
    metadata_json TEXT,      -- métadonnées riches des recherches (date, zone, tailles, météo, URLs...)
    typology_json TEXT,      -- typologie leurre vérifiée, préservée à travers les exports
    fingerprint TEXT UNIQUE, -- anti-doublon stable pour imports de recherches/logs
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS observation_tags (
    observation_id INTEGER NOT NULL REFERENCES observations(id),
    tag_id INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (observation_id, tag_id)
);

CREATE TABLE IF NOT EXISTS lures (
    id INTEGER PRIMARY KEY,
    species_id INTEGER NOT NULL REFERENCES species(id),
    name TEXT NOT NULL,
    type TEXT,
    rank INTEGER DEFAULT 99
);

CREATE TABLE IF NOT EXISTS combos (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    setup_json TEXT          -- matériel voyage : canne, moulinet, PE, plages de lancer et rôle
);

CREATE TABLE IF NOT EXISTS lure_combo (
    lure_id INTEGER NOT NULL REFERENCES lures(id),
    combo_id INTEGER NOT NULL REFERENCES combos(id),
    PRIMARY KEY (lure_id, combo_id)
);

CREATE TABLE IF NOT EXISTS trip_stops (
    id INTEGER PRIMARY KEY,
    city TEXT NOT NULL,
    dates TEXT NOT NULL,
    arrival_date TEXT,       -- YYYY-MM-DD, ancre l'affichage sur le séjour
    stay_dates_json TEXT,     -- JSON array YYYY-MM-DD, jours exacts affichés dans le navigateur de marée
    summary_json TEXT,        -- synthèse destination V5 (tendance, spots, marée, typicités)
    target_species TEXT,
    port TEXT
);

CREATE TABLE IF NOT EXISTS trip_briefs (
    stop_id INTEGER PRIMARY KEY REFERENCES trip_stops(id),
    text TEXT NOT NULL,
    generated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trip_intel (
    id INTEGER PRIMARY KEY,
    stop_id INTEGER NOT NULL REFERENCES trip_stops(id),
    category TEXT NOT NULL,  -- field / access / regulation / strategy / context
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

-- Dimensions utilisées par le moteur de décision. Les dimensions non structurées
-- des deep-research sont conservées dans metadata_json pour ne pas polluer le matching.
INSERT OR IGNORE INTO tag_dimensions (name) VALUES
    ('saison'), ('maree'), ('moment_jour'), ('spot_type'),
    ('leurre'), ('comportement'), ('profondeur'), ('temperature_eau'),
    ('couleur_eau'), ('pression_atmo'), ('observation'), ('zone');

-- Les 10 espèces ciblées du voyage
INSERT OR IGNORE INTO species (id, name_jp, name_fr, name_latin, aliases) VALUES
    (1,  'ヒラメ',   'Hirame',   'Paralichthys olivaceus', 'hirame,limande japonaise,flatfish,flounder'),
    (2,  'スズキ',   'Suzuki',   'Lateolabrax japonicus',  'suzuki,seabass,シーバス,bar japonais,fukko,seigo,hirasuzuki'),
    (3,  'ハマチ',   'Hamachi',  'Seriola quinqueradiata', 'hamachi,buri,ブリ,inada,warasa,yellowtail,sériole,yazu'),
    (4,  'アオリイカ','Aori-Ika', 'Sepioteuthis lessoniana','aori,aori-ika,aori_ika,アオリ,calamar,eging,squid'),
    (5,  'クロダイ', 'Kurodai',  'Acanthopagrus schlegelii','kurodai,chinu,チヌ,dorade noire,black seabream'),
    (6,  'マダイ',   'Madai',    'Pagrus major',           'madai,tai,真鯛,dorade royale japonaise,red seabream'),
    (7,  'タチウオ', 'Tachiuo',  'Trichiurus lepturus',    'tachiuo,太刀魚,sabre,hairtail,poisson sabre'),
    (8,  'サバ',     'Saba',     'Scomber japonicus',      'saba,maquereau,mackerel'),
    (9,  'アジ',     'Aji',      'Trachurus japonicus',    'aji,chinchard,ajing,horse mackerel'),
    (10, 'メバル',   'Mebaru',   'Sebastes inermis',       'mebaru,rockfish,mebaring,sébaste');
