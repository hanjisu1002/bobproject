// lib/records.ts
import api from './api';

// const KEY = "records"; // AsyncStorage 사용 안 함

export type RecordItem = {
  id?: string | number;
  menu_id?: number; // Added
  date: string; // YYYY-MM-DD
  menu?: string; // menu_name
  kcal?: number;
  macro?: { carb_g: number; protein_g: number; fat_g: number }; // Changed to grams
};

export async function addRecord(item: RecordItem) {
  try {
    // Assuming a default portion_g for now, as it's not provided by apiInfer
    const portion_g = 100; // Default to 100g
    const meal_type = "lunch"; // Default to lunch, or could be passed from UI

    await api.post('/food_logs', {
      menu_id: item.menu_id,
      portion_g: portion_g,
      meal_type: meal_type,
    });
    console.log("Record added successfully!");
  } catch (error) {
    console.error("Error adding record:", error);
    throw error; // Re-throw to be caught by the caller (upload.tsx)
  }
}

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
      carb_g: acc.carb_g + (it.macro?.carb_g ?? 0),
      protein_g: acc.protein_g + (it.macro?.protein_g ?? 0),
      fat_g: acc.fat_g + (it.macro?.fat_g ?? 0),
    }),
    { carb_g: 0, protein_g: 0, fat_g: 0 }
  );

  return { date: today, items, totalKcal, totalMacro };
}