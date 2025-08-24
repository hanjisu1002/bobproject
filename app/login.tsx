// app/login.tsx
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, View } from "react-native";
import { HelperText, Text, TextInput } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import TinyButton from "../components/TinyButton";
import { saveJSON } from "../lib/storage";
import { palette } from "../theme";
import { authAPI } from "../lib/api";

export default function Login() {
  const [email, setEmail] = useState("test@me.com");
  const [pw, setPw] = useState("pw123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const invalid = !email.includes("@") || !pw;

  const handleEmailChange = (text: string) => {
    setEmail(text);
    if (error) setError(null);
  };

  const handlePwChange = (text: string) => {
    setPw(text);
    if (error) setError(null);
  };

  const onLogin = async () => {
    if (invalid) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await authAPI.login(email, pw);
      
      if (response.data.access_token) {
        await saveJSON("token", response.data.access_token);
        await saveJSON("profile", { email });
        router.replace("/my");
      } else {
        setError("토큰을 받지 못했습니다.");
      }
    } catch (err: any) {
      console.error('로그인 에러:', err);
      setError(err.response?.data?.detail || "로그인에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: palette.bg }}>
      <View>
        <View
          style={{ backgroundColor: palette.primary, height: 96, borderBottomLeftRadius: 16, borderBottomRightRadius: 16 }}
        />
        <Text
          style={{
            position: "absolute",
            alignSelf: "center",
            bottom: 10,
            fontSize: 24,
            fontWeight: "800",
            color: "white",
          }}
        >
          로그인
        </Text>
      </View>

      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1 }}>
        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ paddingHorizontal: 14, paddingTop: 10, paddingBottom: 24, rowGap: 12 }}
        >
          <View style={{ backgroundColor: "#fff", borderRadius: 14, padding: 14, rowGap: 10, elevation: 2 }}>
            <TextInput
              mode="outlined" label="이메일" value={email} onChangeText={handleEmailChange}
              autoCapitalize="none" keyboardType="email-address" dense style={{ marginBottom: -6 }}
            />
            <HelperText type={email ? "info" : "error"} visible={!email}>{email ? "" : "이메일을 입력하세요"}</HelperText>

            <TextInput
              mode="outlined" label="비밀번호" value={pw} onChangeText={handlePwChange}
              secureTextEntry dense style={{ marginBottom: -6 }}
            />
            <HelperText type={pw ? "info" : "error"} visible={!pw}>{pw ? "" : "비밀번호를 입력하세요"}</HelperText>

            {error && (
              <HelperText type="error" visible style={{ textAlign: 'center', fontSize: 14 }}>
                {error}
              </HelperText>
            )}

            <TinyButton 
              title={loading ? "로그인 중..." : "시작하기"} 
              onPress={onLogin} 
              disabled={invalid || loading} 
              primary 
            />
            <TinyButton title="회원가입" onPress={() => router.push("/signup")} />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}