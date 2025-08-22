// app/(tabs)/index.tsx
import { LinearGradient } from "expo-linear-gradient";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Dimensions,
  FlatList,
  RefreshControl,
  View,
} from "react-native";
import { Card, Chip, Text } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import { loadJSON } from "../../lib/storage";
import { recommendAPI } from "../../lib/api";
import { palette, radius, space } from "../../theme";

const W = Dimensions.get("window").width;

type Profile = {
  targetKcal?: number;
  macro?: { carb: number; protein: number; fat: number };
  prefers?: string[];
  allergens?: string[];
};

type MenuItem = {
  id: string;
  name: string;
  kcal: number; // 표시용 kcal (없으면 0)
  macro: { carb: number; protein: number; fat: number }; // % (nutrition가 없으면 폴백)
  category: "한식" | "일식" | "양식" | "샐러드" | "면" | "덮밥" | string;
};

// 카테고리 칩
const CATS = ["전체", "한식", "일식", "양식", "샐러드", "면", "덮밥"] as const;

// nutrition 그램 → %로 환산
function macroPercentFromGrams(n?: {
  carb_g?: number | null;
  protein_g?: number | null;
  fat_g?: number | null;
}) {
  const cg = Number(n?.carb_g ?? 0);
  const pg = Number(n?.protein_g ?? 0);
  const fg = Number(n?.fat_g ?? 0);

  const cKcal = cg * 4;
  const pKcal = pg * 4;
  const fKcal = fg * 9;
  const total = cKcal + pKcal + fKcal;

  if (total <= 0) return { carb: 50, protein: 25, fat: 25 }; // 폴백

  const carb = Math.round((cKcal / total) * 100);
  const protein = Math.round((pKcal / total) * 100);
  let fat = 100 - carb - protein; // 합 100 보정
  if (fat < 0) fat = 0;
  return { carb, protein, fat };
}

export default function Home() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [cat, setCat] = useState<(typeof CATS)[number]>("전체");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // ✅ 실제 추천 결과
  const [items, setItems] = useState<MenuItem[]>([]);

  // 프로필 로드
  useEffect(() => {
    (async () => {
      const p = await loadJSON<Profile | null>("profile", null);
      setProfile(p);
      setLoading(false);
    })();
  }, []);

  // ✅ 추천 불러오기 (백엔드: GET /v1/recommendations)
  const fetchRecommendations = useCallback(
    async (category?: string) => {
      try {
        // kcal_max로 목표 칼로리를 대략 반영 (없으면 미전달)
        const kcalMax =
          typeof profile?.targetKcal === "number" && profile.targetKcal > 0
            ? Math.round(profile.targetKcal)
            : undefined;

        const res = await recommendAPI.getRecommendations(kcalMax);

        // 서버 스키마: { items: [{ menu, nutrition, score }] }
        const mapped: MenuItem[] = (res?.data?.items ?? []).map((it: any, i: number) => {
          const m = it.menu ?? {};
          const n = it.nutrition ?? {};
          const macroPct = macroPercentFromGrams({
            carb_g: n.carb_g,
            protein_g: n.protein_g,
            fat_g: n.fat_g,
          });

          return {
            id: String(m.menu_id ?? m.food_code ?? i + 1),
            name: m.std_name ?? "이름 없음",
            kcal: Math.round(Number(n.energy_kcal ?? 0)),
            macro: macroPct,
            category: (m.category ?? "한식") as MenuItem["category"],
          };
        });

        // 카테고리 필터(클라이언트)
        const filtered =
          category && category !== "전체"
            ? mapped.filter((x) => x.category === category)
            : mapped;

        setItems(filtered);
      } catch (e) {
        console.error("오늘의 추천 불러오기 실패:", e);
        setItems([]); // 실패 시 빈 리스트
      }
    },
    [profile]
  );

  // 첫 로드/카테고리 변경 시
  useEffect(() => {
    if (!loading) fetchRecommendations(cat);
  }, [loading, cat, fetchRecommendations]);

  // 당겨서 새로고침
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchRecommendations(cat);
    setRefreshing(false);
  }, [fetchRecommendations, cat]);

  // 선호 카테고리 약한 정렬
  const data = useMemo(() => {
    const prefers = profile?.prefers ?? [];
    if (!items.length || !prefers.length) return items;
    const copy = [...items];
    copy.sort((a, b) => Number(prefers.includes(b.category)) - Number(prefers.includes(a.category)));
    return copy;
  }, [items, profile]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: palette.bg }}>
      {/* 히어로 헤더 */}
      <View style={{ paddingHorizontal: space(2), paddingTop: space(1) }}>
        <LinearGradient
          colors={["#8B5CF6", "#6D28D9"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={{
            borderRadius: radius.xl,
            paddingVertical: space(3),
            paddingHorizontal: space(3),
          }}
        >
          <Text style={{ color: "white", fontSize: 22, fontWeight: "800" }}>
            오늘의 추천 메뉴
          </Text>
          <Text style={{ color: "white", opacity: 0.9, marginTop: 6 }}>
            {profile?.targetKcal
              ? `목표 ${profile.targetKcal} kcal • C${profile.macro?.carb ?? 50}/P${profile.macro?.protein ?? 25}/F${profile.macro?.fat ?? 25}`
              : "목표를 설정하면 더 정확히 추천해줘요"}
          </Text>
        </LinearGradient>
      </View>

      {/* 카테고리 칩 */}
      <View
        style={{
          paddingHorizontal: space(2),
          paddingTop: space(2),
          flexDirection: "row",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        {CATS.map((c) => (
          <Chip
            key={c}
            selected={cat === c}
            onPress={() => setCat(c)}
            compact
            style={{ backgroundColor: cat === c ? "#EDE9FE" : "#F3F4F6" }}
            textStyle={{
              color: cat === c ? "#6D28D9" : "#111827",
              fontWeight: cat === c ? "700" : "500",
            }}
          >
            {c}
          </Chip>
        ))}
      </View>

      {/* 리스트 (이미지 없음: 텍스트만) */}
      {loading ? (
        <View style={{ padding: space(2), gap: 12 }}>
          {[...Array(4)].map((_, i) => (
            <Card key={i} style={{ borderRadius: radius.lg, padding: 14 }}>
              <View style={{ height: 18, backgroundColor: "#E5E7EB", borderRadius: 6, width: "60%", marginBottom: 8 }} />
              <View style={{ height: 12, backgroundColor: "#E5E7EB", borderRadius: 6, width: "40%" }} />
            </Card>
          ))}
        </View>
      ) : (
        <FlatList
          data={data}
          keyExtractor={(it) => it.id}
          contentContainerStyle={{
            paddingHorizontal: space(2),
            paddingVertical: space(2),
            gap: 12,
            paddingBottom: 24,
          }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          renderItem={({ item }) => (
            <Card style={{ borderRadius: radius.lg, padding: 14 }}>
              <Text style={{ fontSize: 18, fontWeight: "800", color: "#111827" }}>
                {item.name}
              </Text>
              <Text style={{ color: "#4B5563", marginTop: 4 }}>
                {item.category} • {item.kcal ? `${item.kcal} kcal` : "영양정보 없음"}
              </Text>
              <Text style={{ color: "#6B7280", marginTop: 2, fontSize: 12 }}>
                C {item.macro.carb}% · P {item.macro.protein}% · F {item.macro.fat}%
              </Text>
            </Card>
          )}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}