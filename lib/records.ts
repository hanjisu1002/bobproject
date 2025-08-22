// lib/records.ts
import api from './api';

// const KEY = "records"; // AsyncStorage 사용 안 함

export type RecordItem = {
  id?: string | number;
  date: string; // YYYY-MM-DD
  menu?: string; // menu_name
  kcal?: number;
  macro?: { carb: number; protein: number; fat: number };
};

// addRecord 함수는 백엔드에 menu_id를 전달해야 하므로, 현재는 주석 처리합니다.
// 프론트엔드에서 menu_id를 얻는 로직이 필요합니다.
/*
export async function addRecord(item: RecordItem) {
  // 백엔드 API 호출 로직으로 대체 필요
  // 예: await api.post('/food_logs', { menu_id: item.menu_id, portion_g: ..., meal_type: ... });
  console.warn("addRecord: This function needs to be implemented to call the backend API with menu_id.");
  return [];
}
*/

export async function listRecords(): Promise<RecordItem[]> {
  try {
    const response = await api.get('/food_logs/all');
    // 백엔드 FoodLogResponse를 RecordItem으로 매핑
    return response.data.map((log: any) => ({
      id: log.id,
      date: new Date(log.consumed_at).toISOString().slice(0, 10),
      menu: log.menu_name,
      kcal: log.kcal,
      macro: log.macro,
    }));
  } catch (error) {
    console.error("Error fetching all records:", error);
    return [];
  }
}

export async function listRecordsByDate(date: string): Promise<RecordItem[]> {
  try {
    const response = await api.get('/food_logs/by_date', { params: { target_date: date } });
    // 백엔드 FoodLogResponse를 RecordItem으로 매핑
    return response.data.map((log: any) => ({
      id: log.id,
      date: new Date(log.consumed_at).toISOString().slice(0, 10),
      menu: log.menu_name,
      kcal: log.kcal,
      macro: log.macro,
    }));
  } catch (error) {
    console.error(`Error fetching records for date ${date}:`, error);
    return [];
  }
}

export async function getTodaySummary() {
  const today = new Date().toISOString().slice(0, 10);
  const items = await listRecordsByDate(today);

  const totalKcal = items.reduce((sum, it) => sum + (it.kcal ?? 0), 0);
  const totalMacro = items.reduce(
    (acc, it) => ({
      carb: acc.carb + (it.macro?.carb ?? 0),
      protein: acc.protein + (it.macro?.protein ?? 0),
      fat: acc.fat + (it.macro?.fat ?? 0),
    }),
    { carb: 0, protein: 0, fat: 0 }
  );

  return { date: today, items, totalKcal, totalMacro };
}
