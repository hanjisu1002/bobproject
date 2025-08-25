import { Pressable, StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { Text } from "react-native-paper";

import { palette, radius } from "../theme";

type Props = {
  title: string;
  onPress: () => void;
  variant?: "primary" | "outline";
  style?: StyleProp<ViewStyle>;
};

export default function FancyButton({ title, onPress, variant = "primary", style }: Props) {
  if (variant === "outline") {
    return (
      <Pressable style={style} onPress={onPress}>
        <View style={[styles.button, styles.outlineButton]}>
          <Text style={[styles.text, styles.outlineText]}>{title}</Text>
        </View>
      </Pressable>
    );
  }

  return (
    <Pressable style={style} onPress={onPress}>
      <View style={[styles.button, { backgroundColor: palette.primary }]}>
        <Text style={styles.text}>{title}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    height: 54,
    borderRadius: radius.xl,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: palette.primaryDark,
  },
  text: {
    fontSize: 16,
    fontWeight: "700",
    color: "white",
  },
  outlineButton: {
    backgroundColor: "white",
  },
  outlineText: {
    color: palette.text,
  },
});