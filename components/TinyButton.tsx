// components/TinyButton.tsx
import React from "react";
import { Pressable, Text } from "react-native";
import { palette } from "../theme"; // Import palette

type Props = {
  title: string;
  onPress: () => void;
  outline?: boolean; // 기본: true
  primary?: boolean; // 보라 실버튼
  disabled?: boolean;
};

export default function TinyButton({
  title,
  onPress,
  outline = true,
  primary = false,
  disabled,
}: Props) {
  return (
    <Pressable
      onPress={disabled ? undefined : onPress}
      style={({ pressed }) => ({
        backgroundColor: primary
          ? (pressed ? palette.primaryDark : palette.primary) // Use palette colors
          : outline
          ? (pressed ? "#F3F4F6" : "#FFFFFF") // 아웃라인 기본
          : (pressed ? "#EDE9FE" : "#F5F3FF"),
        borderWidth: outline ? 1 : 0,
        borderColor: outline ? "#E5E7EB" : "transparent",
        borderRadius: 12,
        paddingVertical: 10,
        alignItems: "center",
        opacity: disabled ? 0.5 : 1,
      })}
    >
      <Text
        style={{
          color: primary ? "#FFFFFF" : (outline ? palette.primary : "#4B5563"), // Use palette.primary for outline text
          fontWeight: "700",
          fontSize: 15,
        }}
      >
        {title}
      </Text>
    </Pressable>
  );
}