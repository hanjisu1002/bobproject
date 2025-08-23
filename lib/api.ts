import axios from 'axios';
import { loadJSON } from './storage'; // loadJSON import 추가

// 기존 백엔드 API 설정
const API_BASE_URL = 'http://localhost:8000/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // 쿠키 포함 (CORS credentials)
});

// 요청 인터셉터: 토큰 자동 추가
api.interceptors.request.use(async (config) => {
  const token = await loadJSON<string | null>("token", null); // 토큰 로드
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 기존 타입 정의
export type Box = { x:number; y:number; w:number; h:number; label?:string; score?:number };

export type InferenceResp = {
  imageUrl: string;
  boxes: Box[];
  menuCandidates: Array<{ name:string; score:number }>;
  nutrition: {
    menu_id: number; // Added
    name: string;
    kcal: number;
    macro: { carb:number; protein:number; fat:number };
    allergens: string[];
  }[];
};

// 백엔드 API 함수들
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
  getMenusByCategory: (category: string) => api.get(`/menu/by_category?category=${category}`), // Add this line
};

export const recommendAPI = {
  getRecommendations: (kcal_max?: number) =>
    api.get('/recommendations', { params: { kcal_max } }),
};

// 데모용: 가짜 응답. 추후 fetch(...)로 교체하면 됨.
export async function apiInfer(form: FormData): Promise<InferenceResp> {
  await new Promise(r => setTimeout(r, 600)); // 로딩 느낌
  return {
    imageUrl: "local-selected",
    boxes: [{ x:0.08, y:0.12, w:0.84, h:0.6, label:"불고기덮밥", score:0.92 }],
    menuCandidates: [
      { name:"불고기덮밥", score:0.92 },
      { name:"소불고기정식", score:0.73 },
      { name:"돼지불고기덮밥", score:0.61 },
    ],
    nutrition: [{
      menu_id: 1, // Placeholder ID
      name:"불고기덮밥",
      kcal: 620,
      macro: { carb:85, protein:23, fat:15 },
      allergens:["대두","밀","계란"]
    }]
  };
}

export default api;