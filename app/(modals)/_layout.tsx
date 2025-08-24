import { Stack } from "expo-router";

export default function ModalLayout() {
  return (
    <Stack
      screenOptions={{
        presentation: "transparentModal", // ← 화면을 덮는 모달 + 뒤 화면이 비침
        headerShown: false,               // ← 모달 헤더 숨김
        contentStyle: { backgroundColor: "transparent" }, // ← 기본 흰 배경 제거(투명)
      }}
    />
  );
}
