# -*- coding: utf-8 -*-
"""
Ultralytics YOLO(ONNX)로 '탐지'만 맡기고,
박스별 크롭 → MobileNet(ONNX) 분류(배치 처리) → (옵션) CLIP 재랭킹(지연 로딩/조건부 스킵) → Top-K 출력
"""
from __future__ import annotations  

import os
import json
import dataclasses
import hashlib
import threading
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

import numpy as np
from PIL import Image
# 무거운 라이브러리들은 함수 내부에서 지연 임포트하여
# 모듈 임포트 시 메모리 사용을 최소화한다.

# --------- 기본 경로 (이 파일의 위치 기준) ---------
CV_DIR = Path(__file__).parent.resolve()

# --------- 분류 전처리 기본값 (ImageNet 스타일) ---------
CLS_IMG_SIZE = 256
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# --------- 지연 로딩을 위한 전역 변수 ---------
_yolo_model = None
_cls_model = None
_clip_model = None
_clip_tokenizer = None
_class_names = None

# --------- 모델 로딩 함수들 (지연 로딩) ---------
def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        print("🔄 YOLO 모델 로딩 중...")
        # 지연 임포트
        from ultralytics import YOLO
        _yolo_model = YOLO(CV_DIR / "onnx_models" / "best.onnx")
        print("✅ YOLO 모델 로딩 완료")
    return _yolo_model

def get_cls_model():
    global _cls_model
    if _cls_model is None:
        print("🔄 분류 모델 로딩 중...")
        _cls_model = load_onnx_session(str(CV_DIR / "onnx_models" / "food_cls.onnx"))
        print("✅ 분류 모델 로딩 완료")
    return _cls_model

def get_clip_model():
    global _clip_model, _clip_tokenizer
    if _clip_model is None:
        print("🔄 CLIP 모델 로딩 중...")
        # 지연 임포트
        import open_clip
        _clip_model, _, _clip_tokenizer = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        print("✅ CLIP 모델 로딩 완료")
    return _clip_model, _clip_tokenizer

def get_class_names():
    global _class_names
    if _class_names is None:
        print("🔄 클래스 이름 로딩 중...")
        _class_names = load_class_names(str(CV_DIR / "data" / "class_names.json"))
        print("✅ 클래스 이름 로딩 완료")
    return _class_names

# ========= 유틸 =========
def softmax(x, tau=1.0, axis=-1):
    x = x / max(float(tau), 1e-8)
    x = x - x.max(axis=axis, keepdims=True)
    ex = np.exp(x)
    return ex / np.clip(ex.sum(axis=axis, keepdims=True), 1e-12, None)


def load_onnx_session(path: str):
    # ORT 세션 옵션 (메모리 최적화)
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC  # 최적화 레벨 낮춤
    so.intra_op_num_threads = 1  # 스레드 수 최소화
    so.inter_op_num_threads = 1
    so.execution_mode = ort.ExecutionMode.ORT_PARALLEL  # 병렬 실행 비활성화
    return ort.InferenceSession(path, sess_options=so, providers=["CPUExecutionProvider"])


def run_onnx(sess: ort.InferenceSession, x: np.ndarray) -> np.ndarray:
    inp = sess.get_inputs()[0].name
    out = sess.run(None, {inp: x})[0]
    return out


def preprocess_cls(pil: Image.Image) -> np.ndarray:
    pil = pil.convert("RGB").resize((CLS_IMG_SIZE, CLS_IMG_SIZE), Image.BILINEAR)
    a = np.asarray(pil).astype(np.float32) / 255.0
    a = (a - MEAN) / STD
    a = a.transpose(2, 0, 1)[None, ...].astype(np.float32, copy=False)
    return a


def preprocess_cls_batch(pil_crops: List[Image.Image]) -> np.ndarray:
    """분류 배치 전처리 (메모리 최적화)"""
    arrs = []
    for pil in pil_crops:
        arrs.append(preprocess_cls(pil))  # (1,C,H,W)
    if not arrs:
        return np.empty((0, 3, CLS_IMG_SIZE, CLS_IMG_SIZE), dtype=np.float32)
    return np.concatenate(arrs, axis=0)  # (N,C,H,W)


def safe_crop(pil_img: Image.Image, x1, y1, x2, y2, min_size: int = 2, pad_ratio: float = 0.08) -> Optional[Image.Image]:
    W, H = pil_img.size
    w, h = (x2 - x1), (y2 - y1)
    dx, dy = w * pad_ratio, h * pad_ratio
    x1p = max(0, int(x1 - dx)); y1p = max(0, int(y1 - dy))
    x2p = min(W, int(x2 + dx)); y2p = min(H, int(y2 + dy))
    if x2p - x1p < min_size or y2p - y1p < min_size:
        return None
    return pil_img.crop((x1p, y1p, x2p, y2p))


def load_class_names(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    if isinstance(obj, list):
        return [str(x) for x in obj]
    if isinstance(obj, dict):
        try:
            items = sorted(((int(k), v) for k, v in obj.items()), key=lambda kv: kv[0])
            names = []
            for _, v in items:
                if isinstance(v, dict):
                    names.append(str(v.get('display') or v.get('name') or v.get('slug') or v))
                else:
                    names.append(str(v))
            return names
        except Exception:
            names = []
            for v in obj.values():
                if isinstance(v, dict):
                    names.append(str(v.get('display') or v.get('name') or v.get('slug') or v))
                else:
                    names.append(str(v))
            return names
    raise ValueError("classes JSON must be list or dict")


# ========= CLIP 텍스트 앙상블 =========
def build_prompts(name: str, use_text_ensemble: bool) -> List[str]:
    name = str(name)
    if not use_text_ensemble:
        return [f"a photo of {name}"]
    return [
        f"{name}",
        f"a photo of {name}",
        f"korean food, {name}",
        f"{name}, close-up",
        f"{name}, food photo",
    ]


def _encode_texts(model, tokenizer, device, prompts: List[str]) -> torch.Tensor:
    with torch.no_grad():
        toks = tokenizer(prompts).to(device)
        txt = model.encode_text(toks)
        txt = txt / txt.norm(dim=-1, keepdim=True)
    return txt


def build_clip_text_feat(class_names: List[str], device='cpu',
                         clip_model='ViT-B-32',
                         pretrained='laion2b_s34b_b79k',
                         use_text_ensemble: bool = True) -> tuple:
    model, _, preprocess = open_clip.create_model_and_transforms(
        clip_model, pretrained=pretrained, device=device
    )
    model.eval()
    tokenizer = open_clip.get_tokenizer(clip_model)
    text_vecs = []
    with torch.no_grad():
        for name in class_names:
            prompts = build_prompts(name, use_text_ensemble)
            E = _encode_texts(model, tokenizer, device, prompts)
            m = E.mean(dim=0)
            m = m / m.norm(dim=-1, keepdim=True)
            text_vecs.append(m)
        text_feat = torch.stack(text_vecs, dim=0)
    return model, preprocess, text_feat


def clip_logits_for_crop(model, preprocess, text_feat, crop_pil, device='cpu') -> np.ndarray:
    with torch.no_grad():
        img = preprocess(crop_pil).unsqueeze(0).to(device)
        img_feat = model.encode_image(img)
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
        logit_scale = model.logit_scale.exp()
        logits = (img_feat @ text_feat.T) * logit_scale
        return logits.squeeze(0).detach().cpu().numpy()


# ========= CLIP 캐싱 =========
def _hash_clip_cfg(names, clip_model, clip_pretrain, use_text_ensemble) -> str:
    payload = {
        "names": list(map(str, names)),
        "clip_model": clip_model,
        "clip_pretrain": clip_pretrain,
        "use_text_ensemble": bool(use_text_ensemble),
    }
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _save_clip_cache(path: str, text_feat: np.ndarray, names: List[str], meta: Dict[str, Any]):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    np.savez(path,
             text_feat=text_feat.astype(np.float32),
             names=np.array(names, dtype=object),
             meta=json.dumps(meta, ensure_ascii=False))


def _load_clip_cache(path: str):
    z = np.load(path, allow_pickle=True)
    text_feat = z["text_feat"]
    names = z["names"].tolist()
    meta = json.loads(z["meta"].item())
    return text_feat, names, meta


def build_or_load_clip(class_names: List[str], cfg) -> tuple:
    dev = "cpu"
    cache_key = _hash_clip_cfg(class_names, cfg.clip_model, cfg.clip_pretrain, cfg.use_text_ensemble)
    if cfg.use_clip and cfg.clip_cache and os.path.exists(cfg.clip_cache):
        try:
            text_feat_np, cached_names, meta = _load_clip_cache(cfg.clip_cache)
            if (cached_names == list(map(str, class_names))
                and meta.get("cache_key") == cache_key
                and meta.get("clip_model") == cfg.clip_model
                and meta.get("clip_pretrain") == cfg.clip_pretrain
                and meta.get("use_text_ensemble") == bool(cfg.use_text_ensemble)):
                text_feat_t = torch.from_numpy(text_feat_np).to(dev)
                model, _, preprocess = open_clip.create_model_and_transforms(
                    cfg.clip_model, pretrained=cfg.clip_pretrain, device=dev
                )
                model.eval()
                return model, preprocess, text_feat_t, dev, True
        except Exception:
            pass
    model, preprocess, text_feat_t = build_clip_text_feat(
        class_names, device=dev,
        clip_model=cfg.clip_model,
        pretrained=cfg.clip_pretrain,
        use_text_ensemble=cfg.use_text_ensemble
    )
    if cfg.use_clip and cfg.clip_cache:
        meta = {
            "cache_key": cache_key,
            "clip_model": cfg.clip_model,
            "clip_pretrain": cfg.clip_pretrain,
            "use_text_ensemble": bool(cfg.use_text_ensemble),
        }
        _save_clip_cache(cfg.clip_cache, text_feat_t.detach().cpu().numpy(), class_names, meta)
    return model, preprocess, text_feat_t, dev, False


# ========= 설정 & 러너 =========
@dataclasses.dataclass
class InferenceConfig:
    # Paths
    det_onnx: str = ""
    cls_onnx: str = ""
    classes_json: str = ""

    # Detection (Ultralytics가 처리)
    det_conf: float = 0.15
    det_iou: float = 0.50
    det_max: int = 2
    imgsz: int = 640
    agnostic_nms: bool = True

    # CLIP
    use_clip: bool = True
    clip_model: str = "ViT-B-32"
    clip_pretrain: str = "laion2b_s34b_b79k"
    use_text_ensemble: bool = True
    alpha: float = 0.10   # final = (1-a)*cls + a*clip
    tau: float = 0.20
    clip_cache: str = ""
    device: str = "cpu"

    # Output
    topk: int = 5


class InferenceRunner:
    def __init__(self, cfg: InferenceConfig):
        self.cfg = cfg
        # YOLO 모델 지연 로딩을 위해 None으로 초기화
        self.det_model = None
        self.cls_sess = load_onnx_session(cfg.cls_onnx)
        self.class_names = load_class_names(cfg.classes_json)

        # ---- CLIP 지연 로딩 준비 (3번) ----
        self.clip_model = None
        self.clip_pre = None
        self.text_feat = None
        self.clip_device = "cpu"
        self._clip_ready = False

    def _ensure_det_model(self):
        """YOLO 감지 모델을 필요할 때 로드합니다."""
        if self.det_model is None:
            print("🔄 YOLO 감지 모델 로딩 중...")
            self.det_model = YOLO(self.cfg.det_onnx, task="detect")
            print("✅ YOLO 감지 모델 로딩 완료")

    def _ensure_clip(self):
        if not self._clip_ready and self.cfg.use_clip:
            (self.clip_model,
             self.clip_pre,
             self.text_feat,
             self.clip_device,
             _) = build_or_load_clip(self.class_names, self.cfg)
            self._clip_ready = True

    def infer(self, image_path: str) -> Dict[str, Any]:
        # --- 모델 로딩 보장 ---
        self._ensure_det_model()
        
        pil = Image.open(image_path).convert("RGB")
        r = self.det_model.predict(
            pil,
            conf=self.cfg.det_conf,
            iou=self.cfg.det_iou,
            max_det=self.cfg.det_max,
            agnostic_nms=self.cfg.agnostic_nms,
            imgsz=self.cfg.imgsz,
            verbose=False
        )[0]

        if r.boxes is None or len(r.boxes) == 0:
            W, H = pil.size
            boxes  = np.array([[0, 0, W, H]], dtype=np.float32)
            scores = np.array([1.0], dtype=np.float32)
            det_cls = None
            print("[dbg] fallback: using full-image box")
        else:
            boxes  = r.boxes.xyxy.cpu().numpy()
            scores = r.boxes.conf.cpu().numpy()
            det_cls = r.boxes.cls.cpu().numpy().astype(int) if r.boxes is not None else None

        # ---- 크롭 수집 ----
        crop_infos = []  # (orig_i, bbox(x1,y1,x2,y2), det_score, crop_pil)
        for i in range(len(scores)):
            x1, y1, x2, y2 = boxes[i]
            det_score = float(scores[i])
            crop = safe_crop(pil, x1, y1, x2, y2, min_size=2)
            if crop is None:
                continue
            crop_infos.append((i, (float(x1), float(y1), float(x2), float(y2)), det_score, crop))

        if not crop_infos:
            return {
                "image": os.path.basename(image_path),
                "num_boxes": 0,
                "alpha": self.cfg.alpha,
                "tau": self.cfg.tau,
                "use_clip": bool(self.cfg.use_clip),
                "use_text_ensemble": bool(self.cfg.use_text_ensemble),
                "results": [],
            }

        # ---- 분류 배치 호출 (2번) ----
        crops = [ci[3] for ci in crop_infos]
        xb = preprocess_cls_batch(crops) if len(crops) > 1 else preprocess_cls(crops[0])
        logits_batch = run_onnx(self.cls_sess, xb).astype(np.float32)  # (N,num) 또는 (1,num)
        if logits_batch.ndim == 1:
            logits_batch = logits_batch[None, :]  # (1,num)

        results = []

        # ---- CLIP 조건부 스킵 판단 (3번)
        # 원칙: 박스가 1개이고 분류 확신이 높으면(CLASS max >= 0.80) CLIP 스킵
        use_clip_now_global = False
        if self.cfg.use_clip:
            if len(crops) == 1:
                p1 = softmax(logits_batch[0], tau=1.0)
                use_clip_now_global = bool(p1.max() < 0.90)
            else:
                use_clip_now_global = True

        if use_clip_now_global:
            self._ensure_clip()

        # ---- 각 박스별 Top-K 생성 ----
        eps = 1e-12
        for idx, (orig_i, bbox, det_score, crop) in enumerate(crop_infos):
            logits = logits_batch[idx]
            p_cls = softmax(logits, tau=1.0)

            # CLIP 혼합 (조건부 스킵)
            if use_clip_now_global:
                clip_logits = clip_logits_for_crop(
                    self.clip_model, self.clip_pre, self.text_feat,
                    crop, device=self.clip_device
                )
                # Z-정규화 + temperature
                mu, sd = clip_logits.mean(), clip_logits.std()
                clip_norm = (clip_logits - mu) / (sd + 1e-6)
                clip_norm = np.clip(clip_norm, -3.0, 3.0)
                p_final = (1.0 - self.cfg.alpha) * np.log(p_cls + eps) + self.cfg.alpha * (clip_norm / self.cfg.tau)
                p_clip = (clip_norm / self.cfg.tau)
            else:
                p_clip = None
                p_final = np.log(p_cls + eps)

            C = p_final.shape[0]
            kk = min(self.cfg.topk, C)
            # 보기 쉬운 표시 확률(softmax of p_final)
            disp = p_final - p_final.max()
            disp = np.exp(disp); disp = disp / (disp.sum() + 1e-12)

            top_idx = np.argsort(p_final)[::-1][:kk]
            top = []
            for j in top_idx:
                item = {
                    "label_id": int(j),
                    "label": self.class_names[j] if j < len(self.class_names) else f"class_{j}",
                    "score": float(p_final[j]),
                    "display_prob": float(disp[j]),
                    "cls_score": float(p_cls[j])
                }
                if p_clip is not None:
                    item["clip_score"] = float(p_clip[j])
                top.append(item)

            res = {
                "box_id": int(orig_i),               # 원래 박스 인덱스 유지
                "bbox": list(map(float, bbox)),
                "det_score": float(det_score),
                "topk": top,
            }
            if det_cls is not None and orig_i < len(det_cls):
                res["det_cls_id"] = int(det_cls[orig_i])
            results.append(res)

        return {
            "image": os.path.basename(image_path),
            "num_boxes": len(results),
            "alpha": self.cfg.alpha,
            "tau": self.cfg.tau,
            "use_clip": bool(self.cfg.use_clip),
            "use_text_ensemble": bool(self.cfg.use_text_ensemble),
            "results": results,
        }

    def predict_topk_labels(self, image_path: str, k: int = 3) -> dict:
        """
        이미지 1장에 대해:
        - per_box: 탐지된 각 박스별 top-k 후보 (라벨명/표기확률 포함)
        - flat_topk: 박스들을 합산(표기확률 합)한 전역 top-k
        """
        out = self.infer(image_path)

        per_box = []
        agg: Dict[int, float] = {}

        for r in out["results"]:
            box_topk = r["topk"][:k]
            per_box.append({
                "bbox": r["bbox"],
                "det_score": r["det_score"],
                "labels": [
                    {
                        "label_id": item["label_id"],
                        "label": item["label"],
                        "prob": item["display_prob"],
                        "cls_prob": item["cls_score"],
                    } for item in box_topk
                ]
            })
            for item in box_topk:
                lid = item["label_id"]
                agg[lid] = agg.get(lid, 0.0) + float(item["display_prob"])

        flat_sorted = sorted(agg.items(), key=lambda x: x[1], reverse=True)[:k]
        flat_topk = [
            {
                "label_id": lid,
                "label": self.class_names[lid] if lid < len(self.class_names) else f"class_{lid}",
                "score": score
            }
            for lid, score in flat_sorted
        ]

        return {
            "image": out["image"],
            "per_box": per_box,
            "flat_topk": flat_topk,
        }


# ========= 싱글톤 & 외부용 함수 =========
_runner_singleton: Optional[InferenceRunner] = None
_lock = threading.Lock()

def _get_runner() -> InferenceRunner:
    """
    전역 싱글톤 러너를 반환한다.
    ONNX/CLIP 자원을 재사용하여 반복 호출 비용을 줄인다.
    멀티스레드 환경에서도 안전하게 초기화한다.
    """
    global _runner_singleton
    if _runner_singleton is None:
        with _lock:
            if _runner_singleton is None:
                print("🔄 CV 모델 초기화 중...")
                cfg = InferenceConfig(
                    det_onnx=str(CV_DIR / "onnx_models/best.onnx"),
                    cls_onnx=str(CV_DIR / "onnx_models/food_cls.onnx"),
                    classes_json=str(CV_DIR / "data/class_names.json"),
                    det_conf=0.15, det_iou=0.50, det_max=2, imgsz=640, agnostic_nms=True,
                    use_clip=False,  # CLIP 비활성화로 메모리 절약
                    use_text_ensemble=False,  # 텍스트 앙상블 비활성화
                    clip_cache=str(CV_DIR / "cache/clip_text_feat_vitb32_ens.npz"),
                    alpha=0.10, tau=0.20, device="cpu",
                    topk=3,  # top-k 줄임
                )
                _runner_singleton = InferenceRunner(cfg)
                print("✅ CV 모델 초기화 완료")
    return _runner_singleton


def predict_menu_top3(image_path: str) -> dict:
    """
    다른 파일에서 import 해서 바로 사용:
        from your_module import predict_menu_top3
        result = predict_menu_top3("path/to.jpg")
    반환:
        {
          "image": "...",
          "per_box": [ { "bbox": [...], "det_score": .., "labels": [ { "label": "...", ... } ] }, ... ],
          "flat_topk": [ { "label": "...", "score": ... }, ... ]
        }
    """
    try:
        runner = _get_runner()
        return runner.predict_topk_labels(image_path, k=3)
    except Exception as e:
        print(f"❌ CV 추론 실패: {e}")
        # 폴백: 기본 응답
        return {
            "image": os.path.basename(image_path),
            "per_box": [],
            "flat_topk": [
                {"label": "음식", "score": 0.8},
                {"label": "식사", "score": 0.6},
                {"label": "요리", "score": 0.4}
            ]
        }

def predict_menu_top3_names(image_path: str) -> List[str]:
    """
    간단한 이름만 반환하는 함수 (메모리 절약)
    """
    try:
        result = predict_menu_top3(image_path)
        return [item["label"] for item in result["flat_topk"]]
    except Exception as e:
        print(f"❌ CV 이름 추출 실패: {e}")
        return ["음식", "식사", "요리"]
        


def predict_menu_top3_per_box(image_path: str) -> List[List[str]]:
    """
    이미지 1장을 넣으면, 탐지된 각 박스(메뉴 후보)별로 top3 라벨명을 반환한다.
    Returns:
        list[list[str]]: 예) [[ "삼겹살", "돼지갈비", "불고기" ],
                           [ "물냉면", "비빔냉면", "막국수" ]]
    """
    out = predict_menu_top3(image_path)
    return [
        [cand["label"] for cand in box["labels"]]
        for box in out["per_box"]
    ]


def predict_menu_top3_names(image_path: str) -> List[str]:
    """
    이미지 전체(모든 박스 후보를 합산) 기준으로 최종 top3 라벨명만 간단히 반환.
    NOTE:
      - 여러 메뉴(박스)가 있어도 전역 합산 기준의 top3를 반환한다.
      - 각 박스별 top3가 필요하면 predict_menu_top3_per_box() 사용.
    """
    out = predict_menu_top3(image_path)
    return [x["label"] for x in out["flat_topk"]]


# 외부 공개 심플하게
__all__ = [
    "predict_menu_top3",
    "predict_menu_top3_per_box",
    "predict_menu_top3_names",
    "InferenceConfig",
    "InferenceRunner",
]
