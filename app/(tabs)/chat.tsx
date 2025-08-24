// app/(tabs)/chat.tsx
import { useLocalSearchParams } from "expo-router";
import Chat from "@/components/Chat";

export default function ChatScreen() {
  const { mealName } = useLocalSearchParams<{ mealName?: string }>();
  return <Chat mealName={mealName ?? "이번 식사"} />;
}
