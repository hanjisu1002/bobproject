-- PostgreSQL용 스키마

-- 1) 메뉴 (foods.csv)
CREATE TABLE IF NOT EXISTS menu (
  menu_id        SERIAL PRIMARY KEY,
  food_code      TEXT NOT NULL UNIQUE,
  slug           TEXT NOT NULL UNIQUE,
  std_name       TEXT NOT NULL,
  category       TEXT,
  std_name_norm  TEXT GENERATED ALWAYS AS (
    lower(replace(replace(replace(replace(std_name,' ',''),'-',''),'_',''),'/',''))
  ) STORED,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  updated_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_menu_std_name_norm ON menu(std_name_norm);

-- 2) 영양 (nutrients.csv)
CREATE TABLE IF NOT EXISTS nutrition (
  id           SERIAL PRIMARY KEY,
  food_code    TEXT NOT NULL REFERENCES menu(food_code) ON DELETE CASCADE,
  energy_kcal  REAL,
  water_g      REAL,
  protein_g    REAL,
  fat_g        REAL,
  carb_g       REAL,
  sugars_g     REAL,
  fiber_g      REAL,
  sodium_mg    REAL,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_nutrition_food_code ON nutrition(food_code);

-- 3) 사용자
CREATE TABLE IF NOT EXISTS "user" (
  user_id        SERIAL PRIMARY KEY,
  email          TEXT NOT NULL UNIQUE,
  password_hash  TEXT NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 4) 세션
CREATE TABLE IF NOT EXISTS session (
  token      TEXT PRIMARY KEY,
  user_id    INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5) 프로필
CREATE TABLE IF NOT EXISTS user_profile (
  user_id           INTEGER PRIMARY KEY REFERENCES "user"(user_id) ON DELETE CASCADE,
  daily_kcal_target INTEGER,
  macro_json        JSONB,        -- JSONB 타입으로 변경
  activity_level    TEXT,
  is_completed      BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- 6) 선호
CREATE TABLE IF NOT EXISTS user_preferences (
  user_id                  INTEGER PRIMARY KEY REFERENCES "user"(user_id) ON DELETE CASCADE,
  exclude_allergens_json   JSONB DEFAULT '[]'::jsonb,
  diet_types_json          JSONB DEFAULT '[]'::jsonb,
  like_cuisines_json       JSONB DEFAULT '[]'::jsonb,
  dislike_items_json       JSONB DEFAULT '[]'::jsonb,
  updated_at               TIMESTAMPTZ DEFAULT NOW()
);

-- 7) 히스토리
CREATE TABLE IF NOT EXISTS user_history (
  id       SERIAL PRIMARY KEY,
  user_id  INTEGER NOT NULL REFERENCES "user"(user_id)  ON DELETE CASCADE,
  menu_id  INTEGER NOT NULL REFERENCES menu(menu_id)  ON DELETE CASCADE,
  action   TEXT    NOT NULL CHECK (action IN ('view','select','dismiss','scan')),
  ts       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_history_user_ts ON user_history(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_history_menu_ts ON user_history(menu_id, ts);

-- 8) 피드백
CREATE TABLE IF NOT EXISTS feedback (
  id       SERIAL PRIMARY KEY,
  user_id  INTEGER NOT NULL REFERENCES "user"(user_id) ON DELETE CASCADE,
  reco_id  TEXT,
  score    INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
  message  TEXT,
  ts       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_feedback_user_ts ON feedback(user_id, ts);
CREATE INDEX IF NOT EXISTS idx_feedback_reco_id ON feedback(reco_id);
