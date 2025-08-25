# app/services/cv_runtime.py
from __future__ import annotations

import os
import logging
from pathlib import Path
from fastapi import FastAPI
import onnxruntime as ort

log = logging.getLogger("app.cv")

def _ort_session(model_path: Path) -> ort.InferenceSession:
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = int(os.getenv("ORT_INTRA_OP", "1"))
    opts.inter_op_num_threads = int(os.getenv("ORT_INTER_OP", "1"))
    opts.enable_mem_pattern = False
    opts.enable_cpu_mem_arena = False
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
    return ort.InferenceSession(
        str(model_path),
        sess_options=opts,
        providers=["CPUExecutionProvider"],
    )

def init_cv(app: FastAPI):
    # BLAS 스레드 제한 (메모리/스레드 폭주 방지)
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")

    # 토글
    USE_ULTRA     = os.getenv("USE_ULTRA", "0") == "1"   # 로컬 YOLO 디버그 용
    USE_ONNX_DET  = os.getenv("USE_ONNX_DET", "1") == "1"
    USE_ONNX_CLS  = os.getenv("USE_ONNX_CLS", "1") == "1"

    # 경로
    ROOT = Path(__file__).resolve().parents[2]  # .../project/src
    models_dir = Path(os.getenv("MODELS_DIR", ROOT / "cv" / "onnx_models"))

    # YOLO (옵션: 로컬 디버그 권장, 프로덕션은 비활성화)
    if USE_ULTRA:
        try:
            from ultralytics import YOLO
            app.state.yolo = YOLO(os.getenv("YOLO_WEIGHTS", "yolov8n.pt"))
            log.info("[CV] Ultralytics YOLO loaded")
        except Exception as e:
            log.exception("[CV] YOLO load failed: %s", e)
            raise

    # ONNX: 토글에 따라 각각 로드
    if USE_ONNX_DET:
        det_path = Path(os.getenv("DET_ONNX_PATH", models_dir / "yolov8n.onnx"))
        if not det_path.exists():
            raise FileNotFoundError(f"Detector ONNX not found: {det_path}")
        app.state.det_sess = _ort_session(det_path)
        log.info("[CV] ONNX detector loaded: %s", det_path)

    if USE_ONNX_CLS:
        # int8가 있으면 우선 사용
        cls_default = models_dir / "best.onnx"
        cls_int8 = models_dir / "best.int8.onnx"
        cls_path = Path(os.getenv("CLS_ONNX_PATH", cls_int8 if cls_int8.exists() else cls_default))
        if not cls_path.exists():
            raise FileNotFoundError(f"Classifier ONNX not found: {cls_path}")
        app.state.cls_sess = _ort_session(cls_path)
        log.info("[CV] ONNX classifier loaded: %s", cls_path)

def get_sessions(app: FastAPI):
    """ONNX 세션 요청. YOLO 모드만 사용하는 경우 (None, None) 허용."""
    det = getattr(app.state, "det_sess", None)
    cls = getattr(app.state, "cls_sess", None)

    if det is None or cls is None:
        # YOLO만 쓰는 모드라면 세션 없어도 진행 허용
        if getattr(app.state, "yolo", None) is not None:
            return None, None
        raise RuntimeError("ONNX sessions not initialized (det_sess/cls_sess missing)")
    return det, cls
