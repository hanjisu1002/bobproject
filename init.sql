PRAGMA foreign_keys = ON;

-- 1) 메뉴 (foods.csv)
CREATE TABLE IF NOT EXISTS menu (
  menu_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  food_code      TEXT NOT NULL UNIQUE,
  slug           TEXT NOT NULL UNIQUE,
  std_name       TEXT NOT NULL,
  category       TEXT,
  std_name_norm  TEXT GENERATED ALWAYS AS (
    lower(replace(replace(replace(replace(std_name,' ',''),'-',''),'_',''),'/',''))
  ) STORED,
  created_at     TEXT DEFAULT (datetime('now')),
  updated_at     TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_menu_std_name_norm ON menu(std_name_norm);

-- 2) 영양 (nutrients.csv)
CREATE TABLE IF NOT EXISTS nutrition (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  food_code    TEXT NOT NULL REFERENCES menu(food_code) ON DELETE CASCADE,
  energy_kcal  REAL,
  water_g      REAL,
  protein_g    REAL,
  fat_g        REAL,
  carb_g       REAL,
  sugars_g     REAL,
  fiber_g      REAL,
  sodium_mg    REAL,
  created_at   TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nutrition_food_code ON nutrition(food_code);

-- 3) 사용자
CREATE TABLE IF NOT EXISTS user (
  user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  email          TEXT NOT NULL UNIQUE,
  password_hash  TEXT NOT NULL,
  created_at     TEXT DEFAULT (datetime('now'))
);

-- 4) 세션
CREATE TABLE IF NOT EXISTS session (
  token      TEXT PRIMARY KEY,
  user_id    INTEGER NOT NULL REFERENCES user(user_id) ON DELETE CASCADE,
  created_at TEXT DEFAULT (datetime('now'))
);

-- 5) 프로필
CREATE TABLE IF NOT EXISTS user_profile (
  user_id           INTEGER PRIMARY KEY REFERENCES user(user_id) ON DELETE CASCADE,
  daily_kcal_target INTEGER,
  macro_json        TEXT,        -- JSON 문자열
  activity_level    TEXT,
  is_completed      INTEGER NOT NULL DEFAULT 0,  -- 0/1
  updated_at        TEXT DEFAULT (datetime('now'))
);

-- 6) 선호
CREATE TABLE IF NOT EXISTS user_preferences (
  user_id                  INTEGER PRIMARY KEY REFERENCES user(user_id) ON DELETE CASCADE,
  exclude_allergens_json   TEXT DEFAULT '[]',
  diet_types_json          TEXT DEFAULT '[]',
  like_cuisines_json       TEXT DEFAULT '[]',
  dislike_items_json       TEXT DEFAULT '[]',
  updated_at               TEXT DEFAULT (datetime('now'))
);

-- 7) 히스토리
CREATE TABLE IF NOT EXISTS user_history (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id  INTEGER NOT NULL REFERENCES user(user_id)  ON DELETE CASCADE,
  menu_id  INTEGER NOT NULL REFERENCES menu(menu_id)  ON DELETE CASCADE,
  action   TEXT    NOT NULL CHECK (action IN ('view','select','dismiss','scan')),
  ts       TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_history_user_ts ON user_history(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_history_menu_ts ON user_history(menu_id, ts);