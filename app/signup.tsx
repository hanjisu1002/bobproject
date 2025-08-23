// app/signup.tsx
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { useState, useEffect, use } from "react";
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, View, Alert } from "react-native";
import { HelperText, IconButton, SegmentedButtons, Text, TextInput } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import MacroDialog from "../components/MacroDialog";
import MultiSelectDialog from "../components/MultiSelectDialog";
import { saveJSON } from "../lib/storage";
import type { Profile } from "../lib/types";
import { palette } from "../theme";
import { authAPI, userAPI, menuAPI } from "../lib/api";

const ALLERGEN_OPTIONS = ["계란", "우유", "땅콩", "대두", "밀", "갑각류", "생선", "돼지고기", "소고기"];

type Macro = { carb: number; protein: number; fat: number };

export default function Signup() {
  const router = useRouter();

  // 입력값 (초기 전부 빈값)
  const [name, setName] = useState<string>(""); // 이름 필드 추가
  const [email, setEmail] = useState<string>("test@me.com");
  const [pw, setPw] = useState<string>("pw123");
  const [sex, setSex] = useState<Profile["sex"] | "">("");   // ← 빈 문자열 허용
  const [age, setAge] = useState<string>("25");
  const [target, setTarget] = useState<string>("2000");
  const [macro, setMacro] = useState<Macro>({ carb: 50, protein: 25, fat: 25 });         // 기본값 설정
  const [prefers, setPrefers] = useState<string[]>([]);
  const [allergens, setAllergens] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // 다이얼로그 on/off
  const [openPref, setOpenPref] = useState(false);
  const [openAller, setOpenAller] = useState(false);
  const [openMacro, setOpenMacro] = useState(false);
  const [categories, setCategories] = useState<string[]>([]);
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await menuAPI.getMenuCategories();
        setCategories(response.data);
      } catch (error) {
        console.error("카테고리를 가져오는 데 실패했습니다:", error);
        setCategories([]); // 실패 시 빈 배열로 설정
      }
    };
    fetchCategories();
  }, []);

  // 유효성
  const ageNum = Number(age);
  const tgtNum = Number(target);
  const invalid =
    !name || // 이름 필드 추가
    !email.includes("@") ||
    !pw ||
    !sex || // 성별 미선택
    isNaN(ageNum) || ageNum < 1 ||
    isNaN(tgtNum) || tgtNum < 800;

  const onSubmit = async () => {
    if (invalid) return;

    setLoading(true);
    try {
      // 1. 회원가입
      const signupResponse = await authAPI.signup(name, email, pw); // name 전달

      if (!signupResponse.data.access_token) {
        Alert.alert("회원가입 실패", "토큰을 받지 못했습니다.");
        return;
      }

      // 2. 토큰 저장
      await saveJSON("token", signupResponse.data.access_token);

      // 3. 프로필 정보 저장
      const profile: Profile = {
        name, // name 필드 추가
        email,
        sex: sex as Profile["sex"],
        age: ageNum,
        targetKcal: tgtNum,
        macro: {
          carb: macro.carb,
          protein: macro.protein,
          fat: macro.fat,
        },
        prefers,
        allergens,
      };

      await saveJSON("profile", profile);

      // 4. 백엔드에 프로필 정보 전송
      try {
        await userAPI.updateProfile({
          sex: sex as string, // sex 전달
          age: ageNum, // age 전달
          daily_kcal_goal: tgtNum,
          activity_level: "mid", // 기본값
          macro_ratio: macro, // 탄단지 비율 추가
          exclude_allergens: allergens, // 알레르기 추가
          like_cuisines: prefers, // 선호 카테고리 추가
        });
      } catch (profileError) {
        console.warn('프로필 업데이트 실패:', profileError);
        // 프로필 업데이트 실패해도 로그인은 진행
      }

      router.replace("/");
    } catch (error: any) {
      console.error('회원가입 에러:', error);
      Alert.alert(
        "회원가입 실패",
        error.response?.data?.detail || "회원가입에 실패했습니다."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: palette.bg }}>
      {/* 헤더 */}
      <View>
        <LinearGradient
          colors={[palette.primary, palette.primaryDark]}
          style={{ height: 96, borderBottomLeftRadius: 16, borderBottomRightRadius: 16 }}
        />
        <IconButton
          icon="arrow-left"
          iconColor="white"
          size={24}
          onPress={() => router.back()}
          style={{ position: 'absolute', top: 40, left: 10, zIndex: 1 }}
        />
        <Text style={{ position: "absolute", alignSelf: "center", bottom: 10, fontSize: 24, fontWeight: "800", color: "white" }}>
          회원가입
        </Text>
      </View>

      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1 }}>
        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ paddingHorizontal: 14, paddingTop: 10, paddingBottom: 24, rowGap: 12 }}
        >
          {/* 카드 컨테이너 */}
          <View
            style={{
              backgroundColor: "#fff",
              borderRadius: 14,
              padding: 14,
              rowGap: 10,
              shadowColor: "#000",
              shadowOpacity: 0.06,
              shadowRadius: 6,
              shadowOffset: { width: 0, height: 3 },
              elevation: 2,
            }}
          >
            <TextInput
              mode="outlined"
              label="이름"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
              dense
              style={{ marginBottom: -6 }}
            />
            <HelperText type={name ? "info" : "error"} visible>{name ? "" : "이름을 입력하세요"}</HelperText>

            <TextInput
              mode="outlined"
              label="이메일"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              dense
              style={{ marginBottom: -6 }}
            />
            <HelperText type={email ? "info" : "error"} visible>
              {email ? "" : "이메일을 입력하세요"}
            </HelperText>

            <TextInput
              mode="outlined"
              label="비밀번호"
              value={pw}
              onChangeText={setPw}
              secureTextEntry
              dense
              style={{ marginBottom: -6 }}
            />
            <HelperText type={pw ? "info" : "error"} visible>
              {pw ? "" : "비밀번호를 입력하세요"}
            </HelperText>

            <Text style={{ fontWeight: "700", marginTop: 2 }}>성별</Text>
            <SegmentedButtons
              value={sex}
              onValueChange={(v) => setSex(v as any)}
              buttons={[
                { value: "female", label: "여성" },
                { value: "male", label: "남성" },
              ]}
              density="small"
              style={{ marginBottom: 4 }}
            />

            <View style={{ flexDirection: "row", columnGap: 8 }}>
              <TextInput
                mode="outlined"
                label="나이"
                value={age}
                onChangeText={setAge}
                keyboardType="number-pad"
                dense
                style={{ flex: 1 }}
              />
              <TextInput
                mode="outlined"
                label="목표 칼로리(kcal)"
                value={target}
                onChangeText={setTarget}
                keyboardType="number-pad"
                dense
                style={{ flex: 1 }}
              />
            </View>

            {/* 트리거 버튼들 */}
            <TinyButton title="탄·단·지 비율 선택" onPress={() => setOpenMacro(true)} />
            <TinyButton title="선호 카테고리 선택" onPress={() => setOpenPref(true)} />
            <TinyButton title="알레르기 선택" onPress={() => setOpenAller(true)} />

            {/* 요약(없으면 '-') */}
            <Text style={{ marginTop: 4 }}>
              비율: 탄수화물 {macro.carb}% · 단백질 {macro.protein}% · 지방 {macro.fat}%
            </Text>
            <Text>선호: {prefers.length ? prefers.join(", ") : "없음"}</Text>
            <Text>알레르기: {allergens.length ? allergens.join(", ") : "없음"}</Text>

            <TinyButton title="가입 완료" onPress={onSubmit} disabled={invalid || loading} primary />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {/* 다이얼로그들 */}
      <MacroDialog
        open={openMacro}
        initial={{ carb: macro.carb, protein: macro.protein, fat: macro.fat }}
        onClose={() => setOpenMacro(false)}
        onSave={setMacro}
      />
      <MultiSelectDialog
        title="선호 카테고리"
        options={categories}
        initial={prefers}
        open={openPref}
        onClose={() => setOpenPref(false)}
        onSave={setPrefers}
      />
      <MultiSelectDialog
        title="알레르기"
        options={ALLERGEN_OPTIONS}
        initial={allergens}
        open={openAller}
        onClose={() => setOpenAller(false)}
        onSave={setAllergens}
      />
    </SafeAreaView>
  );
}

/** 작은(컴팩트) 버튼 — 기본은 outline, 눌렀을 때만 색 변함 */
function TinyButton({
  title,
  onPress,
  outline = true,
  primary = false,
  disabled,
}: {
  title: string;
  onPress: () => void;
  outline?: boolean;
  primary?: boolean;
  disabled?: boolean;
}) {
  return (
    <Pressable
      onPress={disabled ? undefined : onPress}
      style={({ pressed }) => ({
        backgroundColor: primary
          ? (pressed ? palette.primaryDark : palette.primary)
          : outline
            ? (pressed ? "#F3F4F6" : "#FFFFFF")
            : (pressed ? "#FEF2E8" : "#FFF7ED"),
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
          color: primary ? "#FFFFFF" : (outline ? palette.primary : palette.text),
          fontWeight: "700",
          fontSize: 15,
        }}
      >
        {title}
      </Text>
    </Pressable>
  );
}