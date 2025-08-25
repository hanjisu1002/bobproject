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
  withCredentials: false, // ❗ 쿠키 미사용 → false
});

// 토큰 자동 주입
api.interceptors.request.use(async (config) => {
  const token = await loadJSON<string | null>('token', null);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// --- 기존 export 들 그대로 ---

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
  // 한글/공백 안전: params 사용
  getMenusByCategory: (category: string) =>
    api.get('/menu/by_category', { params: { category } }),
};

export const recommendAPI = {
  getRecommendations: (kcal_max?: number) =>
    api.get('/recommendations', { params: { kcal_max } }),
};

// ✅ LLM(챗봇) 엔드포인트: 백엔드 라우터가 /v1/chatbot 으로 include되어 있으므로 여기로 보냄
export const chatbotAPI = {
  chat: (message: string, user_id: string) =>
    api.post('/chatbot/chat', { message, user_context: { user_id } }),
};

export default api;
