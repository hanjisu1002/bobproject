import axios from 'axios';
import { loadJSON } from './storage'; // loadJSON import 추가

// 기존 백엔드 API 설정
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE || 'https://bobproject-server.onrender.com/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
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
export type Box = { x: number; y: number; w: number; h: number; label?: string; score?: number };

export type InferenceResp = {
  imageUrl: string;
  boxes: Box[];
  menuCandidates: Array<{ name: string; score: number }>;
  nutrition: {
    menu_id: number; // Added
    name: string;
    kcal: number;
    macro: { carb: number; protein: number; fat: number };
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

// 실제 음식 인식 API 호출 함수
export async function apiInfer(form: FormData): Promise<InferenceResp> {
  try {
    // Axios가 FormData를 감지하고 Content-Type 헤더를 자동으로 설정하도록 headers 속성을 제거합니다.
    const response = await api.post('/vision/recognize-food', form);

    // Backend now returns List[MenuSchema]
    const backend_menus: Array<{ std_name: string; menu_id: number; kcal?: number; macro?: any; allergens?: string[] }> = response.data;

    const menuCandidates = backend_menus.map((menu, index) => ({
      name: menu.std_name, // Use std_name from backend response
      score: 1.0 - (index * 0.1), // 임시 스코어
    }));

    const nutrition = backend_menus.map(menu => ({
      menu_id: menu.menu_id,
      name: menu.std_name,
      kcal: menu.kcal || 0, // Provide default if null
      macro: menu.macro || { carb: 0, protein: 0, fat: 0 }, // Provide default if null
      allergens: menu.allergens || [], // Provide default if null
    }));

    const primaryPrediction = menuCandidates[0]?.name || '인식된 음식';

    return {
      imageUrl: "local-selected",
      boxes: [{ x: 0.08, y: 0.12, w: 0.84, h: 0.6, label: primaryPrediction, score: 0.92 }],
      menuCandidates,
      nutrition: nutrition.length > 0 ? nutrition : [{
        menu_id: 1, // 임시 ID
        name: primaryPrediction,
        kcal: 550, // 임시 칼로리
        macro: { carb: 70, protein: 20, fat: 10 }, // 임시 매크로
        allergens: ["정보 없음"] // 임시 알레르겐
      }]
    };
  } catch (error) {
    console.error("Error during food recognition API call:", error);
    // 에러 발생 시 UI가 깨지지 않도록 비어있거나 기본값을 가진 응답 반환
    return {
      imageUrl: "local-selected",
      boxes: [],
      menuCandidates: [{ name: "인식 실패", score: 0 }],
      nutrition: [],
    };
  }
}

export default api;