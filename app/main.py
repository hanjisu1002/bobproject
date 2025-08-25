from __future__ import annotations

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routers import health, auth, me, menu, recommend, vision, food_log, chatbot
from app.db.session import init_db
from app.core.catalog import Catalog # Add this import

# 로깅 기본 설정 (원하면 settings로 조절)
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("app")

# Render가 주는 포트 (로컬 기본 8000)
PORT = int(os.environ.get("PORT", 8000))

app = FastAPI(title=settings.APP_NAME)

# ---------------------------
# CORS
# ---------------------------
# settings.ALLOWED_ORIGINS = "https://front.vercel.app,https://mydomain.com" 형태 권장
if settings.ALLOWED_ORIGINS:
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
else:
    # 운영에선 특정 도메인만 허용하는 것을 권장
    origins = ["*"]

# Add http://localhost:8081 for local development
if "http://localhost:8081" not in origins:
    origins.append("http://localhost:8081")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# ---------------------------
# 스타트업: DB 초기화 (재시도 포함)
# ---------------------------
@app.on_event("startup")
def _startup():
    init_db()  # 실패해도 앱은 뜬다 (로그 확인)
    app.state.catalog = Catalog() # Initialize and attach the Catalog
    log.info(f"[Startup] API is starting on port {PORT} with origins={origins}")


# ---------------------------
# 라우터
# ---------------------------
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(me.router, prefix=f"{settings.API_PREFIX}/me", tags=["me"])
app.include_router(menu.router, prefix=f"{settings.API_PREFIX}", tags=["menu"])
app.include_router(recommend.router, prefix=f"{settings.API_PREFIX}", tags=["recommendations"])
app.include_router(vision.router, prefix=f"{settings.API_PREFIX}", tags=["vision"])
app.include_router(food_log.router, prefix=f"{settings.API_PREFIX}", tags=["food_logs"])
app.include_router(chatbot.router, prefix=f"{settings.API_PREFIX}", tags=["chatbot"])

# ---------------------------
# 간단한 루트 페이지
# ---------------------------
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Personalized Meal API - Quick Test</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto; margin: 24px; }
    h1 { margin: 0 0 8px; }
    .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin: 12px 0; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin: 6px 0; }
    input, button { padding: 8px 10px; border-radius: 8px; border: 1px solid #e5e7eb; }
    button { cursor: pointer; }
    .links a { margin-right: 12px; }
    pre { background: #0b1020; color: #d1e7ff; padding: 12px; border-radius: 8px; overflow:auto; }
    small { color: #6b7280; }
  </style>
</head>
<body>
  <h1>Personalized Meal API – Quick Test</h1>
  <div class="links">
    <a href="/docs" target="_blank">Swagger Docs</a>
    <a href="/redoc" target="_blank">ReDoc</a>
    <a href="/health" target="_blank">/health</a>
  </div>

  <div class="card">
    <h3>1) 인증</h3>
    <div class="row">
      <input id="email" placeholder="email" value="test@me.com" />
      <input id="pw" placeholder="password" type="password" value="pw123" />
      <button onclick="signup()">/v1/auth/signup</button>
      <button onclick="login()">/v1/auth/login</button>
    </div>
    <div class="row">
      <input id="token" placeholder="access_token (자동 입력됨)" style="min-width:420px"/>
      <small>Bearer 토큰은 아래 호출에 자동 포함돼요.</small>
    </div>
  </div>

  <div class="card">
    <h3>2) 내 프로필/선호</h3>
    <div class="row">
      <button onclick="getProfile()">GET /v1/me/profile</button>
      <input id="kcal" type="number" placeholder="daily_kcal_goal (예: 2000)"/>
      <select id="act">
        <option value="">activity_level</option>
        <option>low</option><option>mid</option><option>high</option>
      </select>
      <button onclick="putProfile()">PUT /v1/me/profile</button>
    </div>
    <div class="row">
      <input id="diet" placeholder='diet_type (vegan/halal/none)'/>
      <button onclick="getPrefs()">GET /v1/me/preferences</button>
      <button onclick="putPrefs()">PUT /v1/me/preferences</button>
    </div>
  </div>

  <div class="card">
    <h3>3) 메뉴/영양/검색</h3>
    <div class="row">
      <input id="menuId" placeholder="menu_id (food_code)" />
      <button onclick="getMenu()">GET /v1/menu/{id}</button>
      <input id="portion" type="number" placeholder="portion_g (예: 300)" />
      <button onclick="getNutri()">GET /v1/menu/{id}/nutrition</button>
    </div>
    <div class="row">
      <input id="q" placeholder="search q (예: 김치, bibim)" />
      <button onclick="searchMenu()">GET /v1/menu/search</button>
      <input id="k" type="number" placeholder="k (유사메뉴 수)" />
      <button onclick="similarMenu()">GET /v1/menu/{id}/similar</button>
    </div>
  </div>

  <div class="card">
    <h3>4) 개인화 추천</h3>
    <div class="row">
      <input id="kmax" type="number" placeholder="kcal_max (예: 700)" />
      <button onclick="reco()">GET /v1/recommendations</button>
      <small>추천은 토큰 필요. 먼저 로그인하세요.</small>
    </div>
  </div>

  <h3>응답</h3>
  <pre id="out">{}</pre>

<script>
async function api(path, opts={}) {
  const t = document.getElementById('token').value.trim();
  const headers = Object.assign(
    {'content-type':'application/json'},
    t ? {'authorization': 'Bearer ' + t} : {}
  );
  const resp = await fetch(path, Object.assign({headers}, opts));
  const text = await resp.text();
  try { return {status: resp.status, json: JSON.parse(text)}; }
  catch { return {status: resp.status, json: text}; }
}
function show(x){ document.getElementById('out').textContent = JSON.stringify(x, null, 2); }

async function signup(){
  const body = { email: document.getElementById('email').value, password: document.getElementById('pw').value };
  const r = await api('/v1/auth/signup', {method:'POST', body: JSON.stringify(body)});
  if (r.status < 400 && r.json && r.json.access_token) {
    document.getElementById('token').value = r.json.access_token;
  }
  show(r);
}
async function login(){
  const body = { email: document.getElementById('email').value, password: document.getElementById('pw').value };
  const r = await api('/v1/auth/login', {method:'POST', body: JSON.stringify(body)});
  if (r.status < 400 && r.json && r.json.access_token) {
    document.getElementById('token').value = r.json.access_token;
  }
  show(r);
}
async function getProfile(){ show(await api('/v1/me/profile')); }
async function putProfile(){
  const kcal = document.getElementById('kcal').value;
  const act  = document.getElementById('act').value || null;
  const body = {};
  if (kcal) body.daily_kcal_goal = Number(kcal);
  if (act) body.activity_level = act;
  show(await api('/v1/me/profile', {method:'PUT', body: JSON.stringify(body)}));
}
async function getPrefs(){ show(await api('/v1/me/preferences')); }
async function putPrefs(){
  const diet = document.getElementById('diet').value || null;
  const body = { diet_type: diet, allergens_exclude: [], like_foods: [], dislike_foods: [], like_countries: [], dislike_countries: [] };
  show(await api('/v1/me/preferences', {method:'PUT', body: JSON.stringify(body)}));
}
async function getMenu(){
  const id = document.getElementById('menuId').value;
  show(await api(`/v1/menu/${encodeURIComponent(id)}`));
}
async function getNutri(){
  const id = document.getElementById('menuId').value;
  const p  = document.getElementById('portion').value;
  const url = p ? `/v1/menu/${encodeURIComponent(id)}/nutrition?portion_g=${encodeURIComponent(p)}` : `/v1/menu/${encodeURIComponent(id)}/nutrition`;
  show(await api(url));
}
async function searchMenu(){
  const q = document.getElementById('q').value;
  show(await api(`/v1/menu/search?q=${encodeURIComponent(q)}`));
}
async function similarMenu(){
  const id = document.getElementById('menuId').value;
  const k  = document.getElementById('k').value;
  const url = k ? `/v1/menu/${encodeURIComponent(id)}/similar?k=${encodeURIComponent(k)}` : `/v1/menu/${encodeURIComponent(id)}/similar`;
  show(await api(url));
}
async function reco(){
  const kmax = document.getElementById('kmax').value;
  const url = kmax ? `/v1/recommendations?kcal_max=${encodeURIComponent(kmax)}` : `/v1/recommendations`;
  show(await api(url));
}
</script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)