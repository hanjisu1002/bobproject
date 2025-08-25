// app/(modals)/chat.tsx
import { View, Pressable } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import Chat from "@/components/Chat";

export default function ChatModal() {
  const router = useRouter();
  const { mealName } = useLocalSearchParams<{ mealName?: string }>();

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
        <Chat mealName={mealName ?? "이번 식사"} />
      </View>
    </View>
  );
}
