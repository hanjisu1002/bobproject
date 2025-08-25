// app/(modals)/chat.tsx
import { View, Pressable } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import Chat, { type FoodRecognitionResult } from "@/components/Chat";

export default function ChatModal() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mealName?: string; fr?: string | string[] }>();
  const mealName = (Array.isArray(params.mealName) ? params.mealName[0] : params.mealName) ?? "이번 식사";

  // fr 파라미터(문자열) → 객체로 복원
  let initialFoodRecognition: FoodRecognitionResult | undefined;
  const frParam = Array.isArray(params.fr) ? params.fr[0] : params.fr;
  if (frParam) {
    try {
        initialFoodRecognition = JSON.parse(decodeURIComponent(frParam)) as FoodRecognitionResult;
    } catch (e) {
        console.warn("Failed to parse FR param:", e);
    }
  }

  return (
    // 반투명 오버레이(뒤 화면 비침)
    <View style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.15)", justifyContent: "flex-end" }}>
      {/* 바깥을 탭하면 닫힘 */}
      <Pressable style={{ position: "absolute", inset: 0 }} onPress={() => router.back()} />

      {/* 아래에서 올라오는 "시트" */}
      <View
        style={{
          height: "92%",                         // ← 살짝 여백 남기기(완전 풀스크린 X)
          borderTopLeftRadius: 20, borderTopRightRadius: 20,
          overflow: "hidden",                    // ← 둥근 모서리에 내용 클리핑
          backgroundColor: "transparent",
        }}
      >
        <Chat mealName={mealName} initialFoodRecognition={initialFoodRecognition} />
      </View>
    </View>
  );
}
