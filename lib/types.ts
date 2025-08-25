// lib/types.ts
export type Profile = {
  user_id: string; // Added
  name?: string; // Added, assuming it's optional from backend
  email: string;
  sex: "male" | "female";
  age: number;
  daily_kcal_goal?: number; // Renamed from targetKcal, made optional
  macro_ratio?: { carb_g: number; protein_g: number; fat_g: number }; // Changed to grams
  activity_level?: "low" | "mid" | "high"; // Added, made optional
  exclude_allergens?: string[]; // Renamed from allergens, made optional
  diet_types?: string[]; // Added, made optional
  like_cuisines?: string[]; // Renamed from prefers, made optional
  dislike_items?: string[]; // Added, made optional
};