import sqlite3, os, pandas as pd, re

BASE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE, "data", "menu.db")
INIT_SQL = os.path.join(BASE, "init.sql")

# 기본 위치: repo/seed/*.csv  → 없으면 /mnt/data/*.csv 로 폴백
FOODS_CSV_CANDIDATES = [
    os.path.join(BASE, "seed", "foods.csv"),
    "/mnt/data/foods.csv",
]
NUTR_CSV_CANDIDATES = [
    os.path.join(BASE, "seed", "nutrients.csv"),
    "/mnt/data/nutrients.csv",
]

def find_csv(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"CSV not found: {candidates}")

def read_csv(path):
    # 인코딩 유연 처리
    for enc in (None, "utf-8-sig", "cp949"):
        try:
            if enc:
                return pd.read_csv(path, encoding=enc)
            else:
                return pd.read_csv(path)
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV: {path}")

# ---------- 정규화 유틸 ----------
def clean_code(x):
    """food_code를 문자열로 정규화: trim, '5199.0' -> '5199' 등"""
    s = str(x).strip()
    # float 문자열 방지
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return s
    except Exception:
        pass
    s = re.sub(r"\.0+$", "", s)  # '5199.00' -> '5199'
    return s

def norm_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    return re.sub(r"[\s\-/_.]+", "", s)

def to_num(v):
    """NaN -> None, 그 외 숫자는 float로"""
    return None if pd.isna(v) else float(v)

def menu_has_generated_std_name_norm(conn: sqlite3.Connection) -> bool:
    # menu 테이블 DDL 문자열을 읽어 std_name_norm이 GENERATED인지 탐지
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='menu'"
    ).fetchone()
    if not row or not row[0]:
        return False
    sql = row[0].lower()
    # std_name_norm 정의부에 generated 키워드가 있으면 True
    return bool(re.search(r"std_name_norm[^,]*generated", sql, re.IGNORECASE))

def main():
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

    foods_path = find_csv(FOODS_CSV_CANDIDATES)
    nutr_path  = find_csv(NUTR_CSV_CANDIDATES)

    df_foods = read_csv(foods_path)
    df_nutr  = read_csv(nutr_path)

    # 컬럼 검증
    required_food_cols = {"food_code", "food_name", "category_name", "slug"}
    required_nutr_cols = {"food_code", "energy_kcal", "water_g", "protein_g", "fat_g",
                          "carb_g", "sugars_g", "fiber_g", "sodium_mg"}

    if not required_food_cols.issubset(set(df_foods.columns)):
        missing = required_food_cols - set(df_foods.columns)
        raise ValueError(f"foods.csv missing columns: {missing}")

    if not required_nutr_cols.issubset(set(df_nutr.columns)):
        missing = required_nutr_cols - set(df_nutr.columns)
        raise ValueError(f"nutrients.csv missing columns: {missing}")

    # ---------- 데이터 정규화 ----------
    # foods
    df_foods["food_code"]     = df_foods["food_code"].map(clean_code)
    df_foods["slug"]          = df_foods["slug"].astype(str).str.strip()
    df_foods["food_name"]     = df_foods["food_name"].astype(str).str.strip()
    df_foods["category_name"] = df_foods["category_name"].astype(str).str.strip()
    df_foods["std_name_norm"] = df_foods["food_name"].map(norm_text)

    # nutrients
    df_nutr["food_code"]      = df_nutr["food_code"].map(clean_code)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        # 스키마 생성/갱신
        conn.executescript(open(INIT_SQL, "r", encoding="utf-8").read())

        # std_name_norm이 GENERATED인지 확인
        std_norm_generated = menu_has_generated_std_name_norm(conn)

        # ---------------- menu 적재 (UPSERT by food_code)
        if std_norm_generated:
            # GENERATED이면 std_name_norm을 INSERT 대상에서 제외
            ins_menu = """
            INSERT INTO menu (food_code, slug, std_name, category, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(food_code) DO UPDATE SET
                slug       = excluded.slug,
                std_name   = excluded.std_name,
                category   = excluded.category,
                updated_at = excluded.updated_at;
            """
            menu_rows = [
                (r["food_code"], r["slug"], r["food_name"], r["category_name"])
                for _, r in df_foods.iterrows()
            ]
        else:
            # 일반 TEXT 컬럼이면 std_name_norm도 함께 적재
            ins_menu = """
            INSERT INTO menu (food_code, slug, std_name, category, std_name_norm, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(food_code) DO UPDATE SET
                slug         = excluded.slug,
                std_name     = excluded.std_name,
                category     = excluded.category,
                std_name_norm= excluded.std_name_norm,
                updated_at   = excluded.updated_at;
            """
            menu_rows = [
                (
                    r["food_code"],
                    r["slug"],
                    r["food_name"],
                    r["category_name"],
                    r["std_name_norm"],
                )
                for _, r in df_foods.iterrows()
            ]

        conn.executemany(ins_menu, menu_rows)

        # ---------------- nutrition 적재
        ins_nutr = """
        INSERT INTO nutrition
          (food_code, energy_kcal, water_g, protein_g, fat_g, carb_g, sugars_g, fiber_g, sodium_mg, created_at)
        VALUES (?,?,?,?,?,?,?,?,?, datetime('now'));
        """

        # FK 대상 존재 여부 확인
        existing_codes = {row[0] for row in conn.execute("SELECT food_code FROM menu").fetchall()}

        nutr_rows, skipped = [], 0
        for _, r in df_nutr.iterrows():
            fc = r["food_code"]
            if fc not in existing_codes:
                skipped += 1
                continue
            nutr_rows.append((
                fc,
                to_num(r.get("energy_kcal")),
                to_num(r.get("water_g")),
                to_num(r.get("protein_g")),
                to_num(r.get("fat_g")),
                to_num(r.get("carb_g")),
                to_num(r.get("sugars_g")),
                to_num(r.get("fiber_g")),
                to_num(r.get("sodium_mg")),
            ))
        if nutr_rows:
            conn.executemany(ins_nutr, nutr_rows)

        conn.commit()

    print("✅ Loaded seed data with normalization")
    print(f"  - menu rows upserted: {len(menu_rows)}")
    print(f"  - nutrition rows inserted: {len(nutr_rows)} (skipped {skipped} rows lacking menu)")

if __name__ == "__main__":
    main()
