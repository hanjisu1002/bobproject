from __future__ import annotations

import os
import time
import logging
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.models.base import Base

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# DB URL 정규화
#  - postgres 접두사 강제: postgresql+psycopg2://
#  - sslmode=require 보장
# ---------------------------------------------------------------------
def _normalize_postgres_url(raw: str) -> str:
    url = raw.strip()

    # 드라이버 접두사 보정
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]
    # 이미 psycopg2 명시되어 있으면 그대로 사용

    # sslmode=require 쿼리 파라미터 보장
    try:
        parsed = urlparse(url)
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if "sslmode" not in q:
            q["sslmode"] = "require"
        new_query = urlencode(q)
        url = urlunparse(parsed._replace(query=new_query))
    except Exception:
        # 파싱 실패시에도 원본을 그대로 사용 (최악의 경우)
        pass

    return url


# ---------------------------------------------------------------------
# DB URL 로드
# ---------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.strip()

IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

if not IS_SQLITE:
    SQLALCHEMY_DATABASE_URL = _normalize_postgres_url(SQLALCHEMY_DATABASE_URL)

# ---------------------------------------------------------------------
# 엔진 생성
#   - sqlite: check_same_thread=False
#   - postgres: pool_pre_ping / recycle
# ---------------------------------------------------------------------
if IS_SQLITE:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,   # 죽은 커넥션 자동 감지
        pool_recycle=300,     # 5분마다 재사용 커넥션 재설정 (idle timeout 대응)
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------
# 안전한 초기화: 재시도(backoff)로 크래시 방지
# ---------------------------------------------------------------------
def init_db(retries: int = 5, base_delay: float = 1.5) -> None:
    """
    테이블 생성 시도. 연결 오류가 나면 지수 백오프하며 재시도.
    실패해도 예외를 올리지 않고 로그만 남긴다(앱 부팅 크래시 방지).
    """
    attempt = 0
    while attempt < retries:
        try:
            Base.metadata.create_all(bind=engine)
            log.info("[DB] Initialized successfully.")
            return
        except OperationalError as e:
            attempt += 1
            delay = base_delay ** attempt  # 1.5, 2.25, 3.375, ...
            log.warning(f"[DB] init failed (attempt {attempt}/{retries}): {e}")
            time.sleep(delay)
        except Exception as e:
            # 스키마 오류 등은 재시도 의미가 적을 수 있으므로 한 번만 로그
            log.exception(f"[DB] init failed due to unexpected error: {e}")
            break

    log.error("[DB] init failed after retries; continuing without blocking startup.")


# ---------------------------------------------------------------------
# 요청 스코프 세션
# ---------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

