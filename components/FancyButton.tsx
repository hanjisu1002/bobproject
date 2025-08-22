import { LinearGradient } from "expo-linear-gradient";
import { Pressable, Text, View, Animated } from "react-native";
import { useEffect, useRef } from "react";
import { palette, radius } from "../theme";

type Props = { title:string; onPress:()=>void; variant?: "primary"|"outline" };

export default function FancyButton({ title, onPress, variant="primary" }:Props){
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const animatePress = (pressed: boolean) => {
    Animated.timing(scaleAnim, {
      toValue: pressed ? 0.97 : 1,
      duration: 120,
      useNativeDriver: true,
    }).start();
  };

  if(variant==="outline"){
    return (
      <Pressable
        onPress={onPress}
        onPressIn={() => animatePress(true)}
        onPressOut={() => animatePress(false)}
        android_ripple={{ color:"#00000011" }}
        style={{ borderWidth:1, borderColor:"#E5E7EB", borderRadius: radius.lg, overflow:"hidden" }}
      >
        <Animated.View style={{ 
          transform: [{ scale: scaleAnim }],
          paddingVertical:14, 
          paddingHorizontal:18, 
          alignItems:"center" 
        }}>
          <Text style={{ fontWeight:"700", color: palette.primary }}>{title}</Text>
        </Animated.View>
      </Pressable>
    );
  }

  // primary (그라데이션 + 그림자)
  return (
    <Pressable
      onPress={onPress}
      onPressIn={() => animatePress(true)}
      onPressOut={() => animatePress(false)}
      android_ripple={{ color:"#ffffff33" }}
      style={{ borderRadius: radius.lg, overflow:"hidden", shadowColor: palette.primary, shadowOpacity:0.25, shadowRadius:10, elevation:4 }}
    >
      <Animated.View style={{ 
        transform: [{ scale: scaleAnim }]
      }}>
        <LinearGradient
          colors={[palette.primary, palette.primaryDark]}
          start={{x:0,y:0}} end={{x:1,y:1}}
          style={{ paddingVertical:14, paddingHorizontal:18, alignItems:"center" }}
        >
          <Text style={{ color:"#fff", fontWeight:"700" }}>{title}</Text>
        </LinearGradient>
      </Animated.View>
    </Pressable>
  );
}
