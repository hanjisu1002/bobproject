
import os
import warnings
from typing import List, Set, Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=FutureWarning)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate, PromptTemplate

# ===== 공통 유틸 =====
def load_api_key() -> None:
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY 가 없습니다. .env에 GOOGLE_API_KEY=... 를 설정하세요."
        )

def normalize_text(s: str) -> str:
    return str(s).strip()

def contains_any(text: str, keys) -> bool:
    return any(k in text for k in keys)

NO_CONTEXT_SINGLE_WORDS = {
    "고마워","감사","감사합니다","땡큐","thanks","thankyou","넵","네","응","예","그래",
    "좋아","맞아","오케이","ok","okk","ㅇㅇ","ㅇㅋ","ㅋ","ㅋㅋ","ㅋㅋㅋ","ㅎㅎ","ㅎㅎㅎ",
    "그래요","맞아요","알겠어","알겠습니다","고마웠어","감사해","굿","굿굿","완료","확인"
}

# ===== 데이터 적재/정규화 =====
STANDARD_COLS = [
    "food_name","serving_size","unit","calories",
    "protein_g","fat_g","carbs_g","sugars_g","sodium_mg",
    "tags","description"
]

def load_and_normalize_data(file_list: List[str]) -> pd.DataFrame:
    all_dfs = []
    for file_path in file_list:
        try:
            df = pd.read_csv(file_path, encoding="utf-8")

            # 다양한 원본 컬럼을 표준화
            if "one_serving_size(g)" in df.columns:
                df = df.rename(columns={
                    "one_serving_size(g)":"serving_size",
                    "energy_kcal":"calories",
                    "carb_g":"carbs_g",
                })
                df["unit"] = "g"
            elif "serving_size(ml)" in df.columns:
                df = df.rename(columns={
                    "serving_size(ml)":"serving_size",
                    "energy_kcal":"calories",
                    "carb_g":"carbs_g",
                })
                df["unit"] = "ml"
            elif "serving_size(g)" in df.columns:
                df = df.rename(columns={
                    "serving_size(g)":"serving_size",
                    "energy_kcal":"calories",
                    "carb_g":"carbs_g",
                })
                df["unit"] = "g"

            df_aligned = pd.DataFrame({c: df[c] for c in STANDARD_COLS if c in df.columns})
            all_dfs.append(df_aligned)
        except FileNotFoundError:
            print(f"❌ 경고: '{file_path}' 없음. 건너뜀.")

    if not all_dfs:
        raise FileNotFoundError("로드할 CSV가 없습니다.")

    master = pd.concat(all_dfs, ignore_index=True)

    # 숫자형 변환
    for col in ["serving_size","calories","protein_g","fat_g","carbs_g","sugars_g","sodium_mg"]:
        if col in master.columns:
            master[col] = pd.to_numeric(master[col], errors="coerce")

    return master

def build_food_name_set(df: pd.DataFrame) -> Set[str]:
    if "food_name" not in df.columns:
        return set()
    return set(df["food_name"].dropna().astype(str).map(normalize_text))

def find_food_in_text(text: str, food_names: Set[str]) -> Optional[str]:
    t = normalize_text(text)
    for name in sorted(food_names, key=len, reverse=True):
        if name and name in t:
            return name
    return None

def get_context_row_by_name(df: pd.DataFrame, name: str) -> Optional[dict]:
    sub = df[df["food_name"] == name]
    if not sub.empty:
        return sub.iloc[0].to_dict()
    return None

def create_rag_retriever(df: pd.DataFrame, embedding_model):
    documents = []
    for _, row in df.iterrows():
        calories_str = "정보 없음" if pd.isna(row.get("calories")) else f"{row['calories']:.1f} kcal"
        row_disp = row.fillna("정보 없음")
        content = (
            f"음식명: {row_disp['food_name']}\n"
            f"1회 제공량: {row_disp['serving_size']}{row_disp.get('unit','g')}\n"
            f"칼로리: {calories_str}\n"
            f"주요 영양소: 단백질 {row_disp['protein_g']}g, 지방 {row_disp['fat_g']}g, 탄수화물 {row_disp['carbs_g']}g\n"
            f"상세 영양소: 당류 {row_disp['sugars_g']}g, 나트륨 {row_disp['sodium_mg']}mg\n"
            f"특징 태그: {row_disp['tags']}\n"
            f"설명: {row_disp['description']}"
        )
        meta = {
            "food_name": row.get("food_name"),
            "serving_size": float(row["serving_size"]) if pd.notna(row.get("serving_size")) else None,
            "unit": (row.get("unit") if pd.notna(row.get("unit")) else "g"),
            "calories": float(row["calories"]) if pd.notna(row.get("calories")) else None,
            "protein_g": float(row["protein_g"]) if pd.notna(row.get("protein_g")) else None,
            "fat_g": float(row["fat_g"]) if pd.notna(row.get("fat_g")) else None,
            "carbs_g": float(row["carbs_g"]) if pd.notna(row.get("carbs_g")) else None,
            "sugars_g": float(row["sugars_g"]) if pd.notna(row.get("sugars_g")) else None,
            "sodium_mg": float(row["sodium_mg"]) if pd.notna(row.get("sodium_mg")) else None,
            "description": row.get("description", "정보 없음"),
            "tags": row.get("tags", "정보 없음"),
        }
        documents.append(Document(page_content=content, metadata=meta))

    vector_store = FAISS.from_documents(documents, embedding_model)
    return vector_store.as_retriever(search_kwargs={"k": 3})

SYSTEM_PROMPT = """
너는 '헬핏(HealthFit)'이라는 이름의 친절하고 전문적인 AI 영양 코치야.
항상 긍정적이고 격려하는 말투를 사용해. 이모지를 적절히 사용해줘. 🍎💪
- 의학적 조언 금지, 마지막에 고지 문구 포함.
- 모든 답변은 한국어.
""".strip()

class Chatbot:
    """
    배포/서버에서 바로 사용 가능한 형태.
    - __init__: 모델/임베딩/데이터/RAG 준비
    - ask(text): 한 턴 입력 → 문자열 응답 반환
    - 상태: current_meal_context, user_profile, consumed_today 보유
    """
    def __init__(
        self,
        csv_files: List[str] = None,
        side_and_drink_files: List[str] = None,
        model_name: str = "gemini-1.5-flash",  # 더 가벼운 모델
        temperature: float = 0.7,
        embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",  # 더 가벼운 임베딩 모델
        device: str = "cpu",
        default_profile: Dict[str, float] = None,
    ):
        load_api_key()

        # LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name, 
            temperature=temperature,
            max_output_tokens=1024,  # 토큰 수 제한
            max_retries=2  # 재시도 횟수 제한
        )

        # Embeddings - 메모리 최적화
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embed_model,
            model_kwargs={"device": device},
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": 8  # 배치 크기 줄임
            }
        )

        # Data
        csv_files = csv_files or ["food_data_description.csv", "drink.csv", "sidedish.csv"]
        self.master_df = load_and_normalize_data(csv_files)
        self.FOOD_NAMES: Set[str] = build_food_name_set(self.master_df)

        side_and_drink_files = side_and_drink_files or ["sidedish.csv", "drink.csv"]
        self.side_and_drink_df = load_and_normalize_data(side_and_drink_files)

        # Retrievers
        self.retriever = create_rag_retriever(self.master_df, self.embeddings)
        self.retriever_side_drink = create_rag_retriever(self.side_and_drink_df, self.embeddings)

        # Prompt/Chain
        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT + "\n\n[검색된 참고 자료]\n{context}"),
            ("user", "{question}")
        ])
        self.rag_chain = (
            # Runnable mapping 없이 간단 호출:
            # context는 retriever.invoke(question)으로 주입
            # 아래 ask()에서 직접 채워서 사용
            self.rag_prompt | self.llm | StrOutputParser()
        )

        # 상태
        self.current_meal_context: Optional[dict] = None
        self.user_profile = default_profile or {"calories":2000, "protein_g":150, "fat_g":60, "carbs_g":215}
        self.consumed_today = {"calories":0.0, "protein_g":0.0, "fat_g":0.0, "carbs_g":0.0, "sugars_g":0.0, "sodium_mg":0.0}

        # 트리거
        self.portion_keywords = ["먹었어","먹음","마셨어","남겼어","반만","절반","두 배","두배","1/2","1/3","2/3","3분의","4분의"]
        self.recommend_triggers = ["곁들여","곁들일","곁들여먹","곁들여 먹","같이","같이 먹","함께","함께 먹","반찬","사이드","사이드디시","추천","뭐 더","뭘 더","뭐랑 같이","뭐랑 함께","같이 먹으면 좋은"]
        self.situational_triggers = ["먹어도 될까","먹어도될까","괜찮을까","괜찮나요","괜찮을지","함께 먹어도","같이 먹어도","먹으면 괜찮","먹어도 괜찮","제로콜라","제로 콜라","콜라","사이다","탄산","디저트","후식","아이스 아메리카노","아메리카노"]
        self.goal_keywords = ["목표","저녁 뭐 먹지","남은 목표","남은 칼로리","남은 단백질","오늘 계획","채워야"]
        self.what_is_it_triggers = ["이 음식이 뭐야","이 음식 뭐야","지금 음식 뭐야","이게 뭐야","지금 음식","현재 음식","이 음식이 뭔데"]

    # ======= 지연 로딩 메서드들 =======
    # @property 데코레이터 제거 - 원래 방식으로 복원
    # def llm(self):
    #     """LLM 모델을 필요할 때만 로드"""
    #     return self._llm

    # def embeddings(self):
    #     """임베딩 모델을 필요할 때만 로드"""
    #     return self._embeddings

    # def retriever(self):
    #     """RAG 검색기를 필요할 때만 생성"""
    #     return self._retriever

    # def retriever_side_drink(self):
    #     """사이드/음료 검색기를 필요할 때만 생성"""
    #     return self._retriever_side_drink

    # def rag_chain(self):
    #     """RAG 체인을 필요할 때만 생성"""
    #     return self._rag_chain

    # ======= 공개 API =======
    def ask(self, user_input: str) -> str:
        """
        프론트/백엔드에서 이 메서드만 호출하면 됩니다.
        입력 한 줄 -> 응답 문자열
        """
        text = normalize_text(user_input)

        # A) 현재 음식 묻기
        if any(t in text for t in self.what_is_it_triggers):
            return self._reply_current_food()

        # B) 목표 기반
        if any(k in text for k in self.goal_keywords):
            return self._handle_goal_planning()

        # C0) 상황/판단형
        if any(t in text for t in self.situational_triggers):
            self._maybe_set_context_from_inline(text)
            if self.current_meal_context:
                return self._handle_situational_question(text)
            return self._need_food_first()

        # C) 곁들일 반찬/음료
        if any(t in text for t in self.recommend_triggers):
            self._maybe_set_context_from_inline(text)
            if self.current_meal_context:
                return self._handle_recommendation()
            return ("헬핏 COACH: 어떤 음식에 곁들일지 먼저 알려주세요! "
                    "(예: 갈비탕 → 같이 먹으면 좋은 음식 추천)\n"
                    "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요.")

        # D) 양 조절
        if any(k in text for k in self.portion_keywords):
            self._maybe_set_context_from_inline(text)
            if self.current_meal_context:
                return self._handle_portion(text)
            return ("헬핏 COACH: 어떤 음식에 대한 양을 조절할까요? 먼저 음식 정보를 알려주세요. "
                    "(예: 비빔냉면 절반만 먹었어)\n"
                    "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요.")

        # E) 일반 RAG
        return self._general_rag(text)

    def set_user_profile(self, profile: Dict[str, float]) -> None:
        self.user_profile.update(profile or {})

    def reset_day(self) -> None:
        self.consumed_today = {k: 0.0 for k in self.consumed_today}
        self.current_meal_context = None

    def get_state(self) -> Dict[str, Any]:
        return {
            "current_food": (self.current_meal_context or {}).get("food_name"),
            "user_profile": self.user_profile,
            "consumed_today": self.consumed_today,
        }

    # ======= 내부 로직 =======
    def _reply_current_food(self) -> str:
        if self.current_meal_context and self.current_meal_context.get("food_name"):
            return (
                f"헬핏 COACH: 지금 이야기 중인 음식은 "
                f"'{self.current_meal_context['food_name']}'이에요! 😄\n"
                "필요하면 양 조절이나 곁들일 음식도 추천해드릴게요.\n"
                "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요."
            )
        return (
            "헬핏 COACH: 아직 특정 음식으로 대화 중이 아니에요. "
            "원하시는 음식 이름을 알려주시면 그걸 기준으로 도와드릴게요! 😊\n"
            "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요."
        )

    def _maybe_set_context_from_inline(self, text: str) -> None:
        if self.current_meal_context is None:
            fname = find_food_in_text(text, self.FOOD_NAMES)
            if fname:
                row = get_context_row_by_name(self.master_df, fname)
                if row:
                    self.current_meal_context = row

    def _handle_portion(self, user_input: str) -> str:
        adjusted = self._portion_adjust(user_input, self.current_meal_context)
        # 누적
        for k, v in adjusted.items():
            if k in self.consumed_today:
                self.consumed_today[k] = float(self.consumed_today.get(k, 0) or 0) + float(v or 0)

        cm = self.current_meal_context or {}
        return (
            "알겠습니다! 말씀하신 내용을 바탕으로 섭취량을 다시 계산해봤어요. 🧐\n"
            f"'{cm.get('food_name','해당 음식')}'의 예상 섭취량은 다음과 같아요.\n\n"
            f"🍕 칼로리: {adjusted.get('calories','계산불가')} kcal\n"
            f"🍞 탄수화물: {adjusted.get('carbs_g','계산불가')} g\n"
            f"🍗 단백질: {adjusted.get('protein_g','계산불가')} g\n"
            f"🥑 지방: {adjusted.get('fat_g','계산불가')} g\n"
            f"🧂 나트륨: {adjusted.get('sodium_mg','계산불가')} mg\n"
            f"\n📈 오늘 누적: {self.consumed_today.get('calories',0):.0f}kcal / "
            f"P{self.consumed_today.get('protein_g',0):.1f} / "
            f"C{self.consumed_today.get('carbs_g',0):.1f} / "
            f"F{self.consumed_today.get('fat_g',0):.1f}\n"
            "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요."
        )

    def _portion_adjust(self, user_input: str, base: dict) -> Dict[str, float]:
        nlu_prompt = PromptTemplate.from_template("""
        문장에서 섭취 비율을 소수점 숫자로만 반환하세요. 다른 말 금지.
        예) 절반=0.5, 두 배=2.0, 3분의 1=0.33, 한 그릇 다=1.0
        문장: '{text}'
        답변:
        """.strip())
        multiplier_str = (nlu_prompt | self.llm | StrOutputParser()).invoke({"text": user_input})
        try:
            m = float(multiplier_str)
        except Exception:
            m = 1.0
        adjusted = {}
        for key in ["calories","protein_g","fat_g","carbs_g","sugars_g","sodium_mg"]:
            val = base.get(key)
            if val is not None and pd.notna(val):
                adjusted[key] = round(float(val) * m, 2)
        return adjusted

    def _handle_recommendation(self) -> str:
        base = self.current_meal_context or {}
        current_food_name = (base.get("food_name") or "").strip()
        keys = ["calories","protein_g","fat_g","carbs_g","sugars_g","sodium_mg"]
        nutri_str = ", ".join(f"{k}={base.get(k,'?')}" for k in keys)

        analysis_prompt = PromptTemplate.from_template(
            "너는 영양 코치야. 음식 이름을 반드시 그대로 포함해, "
            "'{food_name}'의 영양적 특징을 한 문장으로 요약.\n[영양] {nutri}"
        )
        analysis = (analysis_prompt | self.llm | StrOutputParser()).invoke({
            "food_name": current_food_name or "이 음식",
            "nutri": nutri_str
        })

        # 후보 검색
        q = f"{analysis} 보완용 반찬/음료 추천. '{current_food_name}' 제외."
        try:
            docs = self.retriever_side_drink.invoke(q) or []
        except Exception:
            docs = []

        def doc_to_line(d):
            m = getattr(d, "metadata", {}) or {}
            name = (m.get("food_name") or "추천 항목").strip()
            desc = (m.get("description") or "").strip()
            tags = (m.get("tags") or "").strip()
            if not desc:
                pc = getattr(d, "page_content", "") or ""
                for line in pc.splitlines():
                    if line.startswith("설명:"):
                        desc = line.replace("설명:", "").strip()
                        break
            extra = f" (태그: {tags})" if tags else ""
            return name, f"- {name}: {desc}{extra}"

        candidate_lines = []
        seen = set([current_food_name])
        for d in docs:
            nm, line = doc_to_line(d)
            if nm and nm not in seen:
                candidate_lines.append(line)
                seen.add(nm)
                if len(candidate_lines) >= 5:
                    break

        candidates = "\n".join(candidate_lines) if candidate_lines else "- (후보 없음)"
        recommend_prompt = PromptTemplate.from_template(
            "[현재 음식 분석]\n{analysis}\n\n[후보 목록]\n{candidates}\n\n"
            "[지시] 후보에서 2~3개를 골라 '이름 - 한 줄 근거'로 제시. "
            "근거는 후보 설명/태그에서만. 의학적 조언 금지."
        )
        body = (recommend_prompt | self.llm | StrOutputParser()).invoke({
            "analysis": analysis,
            "candidates": candidates
        })
        return f"{analysis}\n\n{body}\n\n※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요."

    def _handle_situational_question(self, user_question: str) -> str:
        main_name = (self.current_meal_context or {}).get("food_name")
        add_name = self._extract_additional_item(user_question, main_name)

        def fetch_ctx(name: str | None):
            if not name: return []
            try:
                return self.retriever.invoke(name) or []
            except Exception:
                return []

        main_docs = fetch_ctx(main_name)
        add_docs  = fetch_ctx(add_name)

        if not main_docs and not add_docs:
            return ("헬핏 COACH: 관련 정보를 찾지 못했어요. 음식 이름을 정확히 알려주시면 "
                    "칼로리·영양·성분 관점에서 판단을 도와드릴게요. 😊\n"
                    "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요.")

        def pack(docs): return "\n\n".join(d.page_content for d in docs)
        blocks = []
        if main_docs: blocks.append(f"[{main_name}] 정보\n{pack(main_docs)}")
        if add_docs:  blocks.append(f"[{add_name}] 정보\n{pack(add_docs)}")
        context = "\n\n---\n\n".join(blocks)

        templ = """
너는 전문 영양 코치 '헬핏'이야. 아래 [참고자료]를 우선 근거로 [질문]에 대해 관점별로 분석하고 결론을 정리해.
1) 수치는 자료에 있을 때만. 2) 일반 상식 수준 보완은 허용. 3) 칼로리/영양균형/건강·성분 관점 불릿.
4) 마지막 고지 문구 포함.

[대상] 주 음식: {main_name}, 추가 항목: {add_name}
[질문] {question}
[참고자료]
{context}
""".strip()
        analysis_prompt = PromptTemplate.from_template(templ)
        ans = (analysis_prompt | self.llm | StrOutputParser()).invoke({
            "main_name": main_name or "(미지정)",
            "add_name": add_name or "(없음)",
            "question": user_question,
            "context": context
        })
        return ans + "\n\n※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요."

    def _extract_additional_item(self, q: str, main_food: Optional[str]) -> Optional[str]:
        t = q.strip()
        if main_food: t = t.replace(main_food, "")
        cand = find_food_in_text(t, self.FOOD_NAMES)
        if cand and cand != main_food:
            return cand
        # LLM 보조 추출
        if main_food:
            extraction_prompt = PromptTemplate.from_template(
                "다음 문장에서 '{main_food}' 외에 추가로 언급된 음식/음료가 있으면 정확히 이름만 하나. 없으면 '없음'.\n문장: {q}"
            )
            add_try = (extraction_prompt | self.llm | StrOutputParser()).invoke({"main_food": main_food, "q": q}).strip().strip("'\"")
            if add_try and add_try not in {"없음","없다","none","null"} and add_try in self.FOOD_NAMES and add_try != main_food:
                return add_try
        return None

    def _need_food_first(self) -> str:
        return ("헬핏 COACH: 어떤 음식에 대해 물으시는지 알려주세요! "
                "예) '갈비탕에 제로콜라 먹어도 될까?'\n"
                "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요.")

    def _handle_goal_planning(self) -> str:
        remaining, exceeded = self._compute_remaining(self.user_profile, self.consumed_today)
        cand_df = self._select_candidates_by_goal(self.master_df, remaining, scope="meal", top_k=12)
        if cand_df.empty:
            return ("헬핏 COACH: 남은 목표와 맞는 후보를 찾기 어려워요. "
                    "칼로리/단백질 목표를 조금 조정하거나, 가벼운 간식부터 채워보는 건 어떨까요? 😊\n"
                    "※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요.")
        picks = self._greedy_pick_with_limits(cand_df, remaining, max_items=3)
        if not picks: picks = [cand_df.iloc[0]]

        lines = []
        total = {"calories":0.0,"protein_g":0.0,"carbs_g":0.0,"fat_g":0.0}
        for r in picks:
            cal = float(r.get("calories") or 0)
            p   = float(r.get("protein_g") or 0)
            c   = float(r.get("carbs_g") or 0)
            f   = float(r.get("fat_g") or 0)
            total["calories"] += cal; total["protein_g"] += p; total["carbs_g"] += c; total["fat_g"] += f
            lines.append(f"• {r['food_name']} — {cal:.0f}kcal, 단백질 {p:.1f}g, 탄수화물 {c:.1f}g, 지방 {f:.1f}g")

        summary = (f"예상 합계: {total['calories']:.0f}kcal, "
                   f"단백질 {total['protein_g']:.1f}g, 탄수화물 {total['carbs_g']:.1f}g, 지방 {total['fat_g']:.1f}g")
        remaining_line = (f"(남은 목표: {remaining.get('calories',0):.0f}kcal / "
                          f"P{remaining.get('protein_g',0):.1f}g / "
                          f"C{remaining.get('carbs_g',0):.1f}g / "
                          f"F{remaining.get('fat_g',0):.1f}g)")

        prompt = PromptTemplate.from_template("""
[현황]
- 오늘 목표: {goal}
- 현재 섭취: {consumed}
- 남은 목표: {remaining_line}

[추천 메뉴(수치 확정)]
{menu_block}
{summary_line}

[지시]
1) 위 숫자들은 확정값. 그대로 사용.
2) 왜 적합한지 3~4줄 설명(단백질/칼로리/당·나트륨 관점).
3) 필요시 대체 1개 제안(숫자 없이).
4) 고지 문구 포함.
""".strip())
        body = (prompt | self.llm | StrOutputParser()).invoke({
            "goal": self.user_profile,
            "consumed": self.consumed_today,
            "remaining_line": remaining_line,
            "menu_block": "\n".join(lines),
            "summary_line": summary
        })
        return body + "\n\n※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요."

    # ===== 수식/후보 선택 헬퍼 =====
    @staticmethod
    def _compute_remaining(user_profile: dict, consumed_today: dict):
        remaining, exceeded = {}, {}
        for k, target in user_profile.items():
            cur = float(consumed_today.get(k, 0) or 0)
            diff = round(target - cur, 2)
            if diff < 0:
                exceeded[k] = -diff; remaining[k] = 0.0
            else:
                remaining[k] = diff
        return remaining, exceeded

    @staticmethod
    def _select_candidates_by_goal(df: pd.DataFrame, remaining: dict, scope: str = "meal", top_k: int = 12) -> pd.DataFrame:
        cand = df.copy()
        if scope == "meal" and "unit" in cand.columns:
            cand = cand[cand["unit"].fillna("").ne("ml")]
        for col in ["calories","protein_g","fat_g","carbs_g","sugars_g","sodium_mg"]:
            if col in cand.columns:
                cand[col] = pd.to_numeric(cand[col], errors="coerce").fillna(0)

        cal_rem = float(remaining.get("calories", 0) or 0)
        if cal_rem > 0:
            cand = cand[cand["calories"] <= max(cal_rem, 120)]  # 최소 허용 버퍼

        eps = 1e-6
        protein_rem = float(remaining.get("protein_g", 0) or 0)
        sodium_rem  = float(remaining.get("sodium_mg", 999999) or 999999)

        protein_density = cand["protein_g"] / (cand["calories"] + eps)
        protein_hit     = np.minimum(cand["protein_g"], protein_rem)
        sugar_pen       = cand["sugars_g"].clip(lower=0)
        sodium_over     = (cand["sodium_mg"] - sodium_rem).clip(lower=0)

        score = (3.0 * protein_hit) + (2.0 * protein_density) - (0.6 * sugar_pen) - (0.8 * (sodium_over / 500.0))
        cand = cand.assign(_score=score).sort_values("_score", ascending=False)
        return cand.head(top_k).drop(columns=["_score"], errors="ignore")

    @staticmethod
    def _greedy_pick_with_limits(cand_df: pd.DataFrame, remaining: dict, max_items: int = 3):
        picks = []
        cal_left = float(remaining.get("calories", 0) or 99999)
        for _, r in cand_df.iterrows():
            c = float(r.get("calories") or 0)
            if c <= cal_left + 1e-6:
                picks.append(r); cal_left -= c
            if len(picks) >= max_items: break
        return picks

    def _general_rag(self, user_input: str) -> str:
        # retriever로 context 먼저 뽑아와서 체인에 주입
        try:
            ctx_docs = self.retriever.invoke(user_input) or []
        except Exception:
            ctx_docs = []
        ctx_text = "\n\n".join(d.page_content for d in ctx_docs) if ctx_docs else "(자료 없음)"
        response = self.rag_chain.invoke({"context": ctx_text, "question": user_input})

        # 컨텍스트 업데이트 가드
        words = user_input.split()
        update_ok = False
        if contains_any(user_input, ["정보","알려줘","칼로리","영양","어때","성분","설명"]):
            update_ok = True
        elif len(words) == 1:
            w = words[0]
            if (w not in NO_CONTEXT_SINGLE_WORDS) and (w in self.FOOD_NAMES):
                update_ok = True
        else:
            fname_inline = find_food_in_text(user_input, self.FOOD_NAMES)
            if fname_inline:
                row = get_context_row_by_name(self.master_df, fname_inline)
                if row:
                    self.current_meal_context = row
                update_ok = False

        if update_ok:
            if len(words) == 1 and words[0] in self.FOOD_NAMES:
                row = get_context_row_by_name(self.master_df, words[0])
                if row: self.current_meal_context = row
            else:
                # 검색 질의로 컨텍스트 잡기
                try:
                    docs = self.retriever.invoke(user_input)
                    if docs:
                        self.current_meal_context = docs[0].metadata
                except Exception:
                    pass

        return f"{response}\n\n※ 본 답변은 참고용이며, 의학적 소견이 필요할 경우 전문가와 상의하세요."


# 선택: 로컬에서 간단 테스트 가능
if __name__ == "__main__":
    bot = Chatbot()
    print("헬핏 COACH 준비 완료. 종료하려면 Ctrl+C.")
    while True:
        q = input("You: ").strip()
        print("헬핏:", bot.ask(q))