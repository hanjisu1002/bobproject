// api.ts
import axios from 'axios';
import { loadJSON } from './storage';

// 항상 EXPO_PUBLIC_API_BASE가 최우선, 없으면 프로덕션 기본값 사용
const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE?.trim() ||
  'https://bobproject-server.onrender.com/v1';

console.log('[API] baseURL =', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false, // 쿠키 미사용 → false
});

// 토큰 자동 주입
api.interceptors.request.use(async (config) => {
  const token = await loadJSON<string | null>('token', null);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ===== 타입들 (화면에서 쓰면 유지) =====
export type Box = { x: number; y: number; w: number; h: number; label?: string; score?: number };

export type InferenceResp = {
  imageUrl: string;
  boxes: Box[];
  menuCandidates: Array<{ name: string; score: number }>;
  nutrition: {
    menu_id: number;
    name: string;
    kcal: number;
    macro: { carb: number; protein: number; fat: number };
    allergens: string[];
  }[];
};

// ===== Auth / User / Menu / Recommend =====
export const authAPI = {
  signup: (name: string, email: string, password: string) =>
    api.post('/auth/signup', { name, email, password }),
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  logout: () => api.post('/auth/logout'),
};

export const userAPI = {
  getProfile: () => api.get('/me/profile'),
  updateProfile: (data: any) => api.put('/me/profile', data),
  getPreferences: () => api.get('/me/preferences'),
  updatePreferences: (data: any) => api.put('/me/preferences', data),
  deleteMe: () => api.delete('/me'),
};

export const menuAPI = {
  getMenu: (id: string) => api.get(`/menu/${id}`),
  getNutrition: (id: string, portion_g?: number) =>
    api.get(`/menu/${id}/nutrition`, { params: { portion_g } }),
  searchMenu: (query: string) => api.get('/menu/search', { params: { q: query } }),
  getSimilarMenu: (id: string, k?: number) =>
    api.get(`/menu/${id}/similar`, { params: { k } }),
  getMenuCategories: () => api.get('/menu/categories'),
  // 한글/공백 안전: params 사용 → 자동 인코딩
  getMenusByCategory: (category: string) =>
    api.get('/menu/by_category', { params: { category } }),
};

export const recommendAPI = {
  getRecommendations: (kcal_max?: number) =>
    api.get('/recommendations', { params: { kcal_max } }),
};

// ✅ 챗봇: 최종 경로는 /v1/chatbot/chat (백엔드 라우터가 /chatbot/chat로 등록되어 있음)
export const chatbotAPI = {
  chat: (message: string, user_id: string) =>
    api.post('/chatbot/chat', { message, user_context: { user_id } }),
};

// ✅ 이미지 인식: 멀티파트 업로드 → 서버의 List[MenuWithNutrition]를 화면 타입으로 변환
export async function apiInfer(form: FormData): Promise<InferenceResp> {
  const res = await api.post('/vision/recognize-food', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  // 백엔드 반환 예: [{ menu_id, std_name, kcal, macro, allergens }]
  const backend_menus: Array<{
    menu_id: number;
    std_name: string;
    kcal?: number;
    macro?: { carb?: number; protein?: number; fat?: number } | null;
    allergens?: string[] | null;
  }> = res.data ?? [];

  const menuCandidates = backend_menus.map((m, i) => ({
    name: m.std_name,
    score: Math.max(0, 1 - i * 0.1), // 임시 스코어
  }));

  const nutrition = backend_menus.map((m) => ({
    menu_id: m.menu_id,
    name: m.std_name,
    kcal: m.kcal ?? 0,
    macro: {
      carb: m.macro?.carb ?? 0,
      protein: m.macro?.protein ?? 0,
      fat: m.macro?.fat ?? 0,
    },
    allergens: m.allergens ?? [],
  }));

  const primary = menuCandidates[0]?.name ?? '인식된 음식';

  return {
    imageUrl: 'local-selected', // 필요 시 서버 URL로 교체
    boxes: [{ x: 0.08, y: 0.12, w: 0.84, h: 0.6, label: primary, score: 0.92 }],
    menuCandidates,
    nutrition,
  };
}

export default api;
