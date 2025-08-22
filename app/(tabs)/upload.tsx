// app/(tabs)/upload.tsx
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import * as ImageManipulator from "expo-image-manipulator";
import * as ImagePicker from "expo-image-picker";
import { useEffect, useMemo, useState } from "react";
import { Image, ScrollView, View } from "react-native";
import { ActivityIndicator, Card, Chip, Divider, Text } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";

import ChatDemo from "../../components/ChatDemo";
import FancyButton from "../../components/FancyButton";
import Section from "../../components/Section";
import { apiInfer, InferenceResp } from "../../lib/api";
import { evaluate } from "../../lib/eval";
import { addRecord } from "../../lib/records";
import { loadJSON } from "../../lib/storage";
import { suggestNextMeal } from "../../lib/suggest";
import { palette, radius, space } from "../../theme";

type Profile = {
  targetKcal?: number;
  macro?: { carb:number; protein:number; fat:number };
  allergens?: string[];
  prefers?: string[];
};

type Step = "select" | "recognize";

export default function Upload() {
  const tabBarH = useBottomTabBarHeight();

  // 단계/데이터 상태
  const [step, setStep] = useState<Step>("select");
  const [uri, setUri] = useState<string | null>(null);

  // 인식/평가/추천 상태
  const [res, setRes] = useState<InferenceResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [evalMsg, setEvalMsg] = useState<{ score:number; advice:string[] } | null>(null);
  const [suggest, setSuggest] = useState<{ title:string; reason:string; items:string[] }[] | null>(null);

  // 사용자 프로필
  const [profile, setProfile] = useState<Profile | null>(null);
  useEffect(() => { (async () => {
    setProfile(await loadJSON<Profile | null>("profile", null));
  })(); }, []);

  const resetInferenceStates = ()=>{
    setRes(null);
    setEvalMsg(null);
    setSuggest(null);
  };

  // ── 1) 이미지 선택/촬영 → 선택되면 자동으로 recognize 단계로 이동 ───────────────
  const pick = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") { alert("앨범 권한이 필요해요."); return; }
    const { canceled, assets } = await ImagePicker.launchImageLibraryAsync({ quality:0.9 });
    if (!canceled && assets?.[0]?.uri){
      setUri(assets[0].uri);
      resetInferenceStates();
      setStep("recognize"); // 다음 단계로 이동
    }
  };

  const snap = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") { alert("카메라 권한이 필요해요."); return; }
    const { canceled, assets } = await ImagePicker.launchCameraAsync({ quality:0.9 });
    if (!canceled && assets?.[0]?.uri){
      setUri(assets[0].uri);
      resetInferenceStates();
      setStep("recognize"); // 다음 단계로 이동
    }
  };

  // ── 2) 인식하기 ─────────────────────────────────────────────────────────────
  const infer = async () => {
    if (!uri) return;
    setLoading(true);
    try{
      // 리사이즈(전송 최적화)
      const resized = await ImageManipulator.manipulateAsync(
        uri, [{ resize: { width: 640 } }],
        { compress: 0.9, format: ImageManipulator.SaveFormat.JPEG }
      );
      const file = { uri: resized.uri, name:"upload.jpg", type:"image/jpeg" } as any;
      const form = new FormData(); form.append("file", file);

      // (현재 데모) 인식 API
      const data = await apiInfer(form);
      setRes(data);

      // 안전한 프로필
      const safe: Required<Profile> = {
        targetKcal: profile?.targetKcal ?? 1800,
        macro: profile?.macro ?? { carb:50, protein:25, fat:25 },
        allergens: profile?.allergens ?? [],
        prefers: profile?.prefers ?? [],
      };

      const picked = data?.nutrition?.[0];
      if (picked) {
        setEvalMsg(
          evaluate(
            { kcal: picked.kcal, macro: picked.macro },
            { targetKcal: safe.targetKcal, macro: safe.macro, allergens: safe.allergens },
            picked.allergens
          )
        );
        setSuggest(
          suggestNextMeal(
            { kcal: picked.kcal, macro: picked.macro, allergens: picked.allergens },
            { targetKcal: safe.targetKcal, macro: safe.macro, prefers: safe.prefers, allergens: safe.allergens }
          )
        );
      } else {
        // 인식 실패 폴백
        setEvalMsg({ score: 80, advice: ["이번 끼니 데이터가 부족하지만 전반적으로 무난해요."] });
        setSuggest([{ title:"다음 끼니 가볍게", reason:"데모 기본 제안", items:["샐러드 + 단백질", "밥 1/2", "소스·당류 줄이기"] }]);
      }
    } finally {
      setLoading(false);
    }
  };

  // 기록 저장
  const saveRecord = async () => {
    if (!res) return;
    const n = res.nutrition[0];
    await addRecord({ date: new Date().toISOString().slice(0,10), menu: n?.name, kcal: n?.kcal, macro: n?.macro });
    alert("오늘 기록에 저장했어요!");
  };

  // 상단 타이틀/가이드
  const title = useMemo(() => step === "select" ? "사진 업로드" : "미리보기", [step]);

  return (
    <SafeAreaView style={{ flex:1, backgroundColor: palette.bg }}>
      <ScrollView
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ padding: space(2), gap: space(2), paddingBottom: tabBarH + 24 }}
      >
        <Text style={{ fontSize: 22, fontWeight: "700" }}>{title}</Text>

        {/* ───────────────────── 1) 선택 단계 ───────────────────── */}
        {step === "select" && (
          <Section>
            <Card
              mode="contained"
              style={{
                height: 260,
                backgroundColor:"#EEF0F6",
                borderRadius: radius.md,
                alignItems:"center",
                justifyContent:"center"
              }}
            >
              <Text style={{ color:"#6B7280" }}>이미지를 선택하거나 촬영해주세요</Text>
            </Card>

            <View style={{ height: 10 }} />
            <FancyButton title="앨범에서 선택" onPress={pick} />
            <View style={{ height: 8 }} />
            <FancyButton title="카메라로 촬영" variant="outline" onPress={snap} />
          </Section>
        )}

        {/* ───────────────────── 2) 인식 단계 ───────────────────── */}
        {step === "recognize" && (
          <>
            <Section>
              {uri ? (
                <Image source={{ uri }} style={{ height: 260, borderRadius: radius.md }} />
              ) : (
                <Card mode="contained" style={{ height: 260, backgroundColor:"#EEF0F6", borderRadius: radius.md, alignItems:"center", justifyContent:"center" }}>
                  <Text style={{ color:"#6B7280" }}>이미지를 먼저 선택해주세요</Text>
                </Card>
              )}
              <View style={{ height: 10 }} />
              <FancyButton title={loading ? "인식 중..." : "인식하기"} onPress={infer} />
              <View style={{ height: 8 }} />
              <FancyButton title="다른 사진 선택" variant="outline" onPress={() => { setStep("select"); setUri(null); resetInferenceStates(); }} />
            </Section>

            {loading && <ActivityIndicator animating size="small" style={{ marginTop: 6 }} />}

            {!!res && (
              <Section title="인식 결과">
                <View style={{ flexDirection:"row", flexWrap:"wrap", gap: 8 }}>
                  {res.menuCandidates.map((m, i)=>(<Chip key={m.name+i} compact selected={i===0}>{m.name}</Chip>))}
                </View>

                <Divider style={{ marginVertical: 10 }} />

                {res.nutrition[0] && (
                  <Card style={{ borderRadius: radius.md }}>
                    <Card.Title title={res.nutrition[0].name} />
                    <Card.Content style={{ gap: 6 }}>
                      <Text>칼로리: {res.nutrition[0].kcal} kcal</Text>
                      <Text>
                        비율: 탄수화물 {res.nutrition[0].macro.carb}% · 단백질 {res.nutrition[0].macro.protein}% · 지방 {res.nutrition[0].macro.fat}%
                      </Text>
                      <Text>알레르겐: {res.nutrition[0].allergens.join(", ") || "없음"}</Text>
                    </Card.Content>
                  </Card>
                )}

                <View style={{ height: 10 }} />
                <FancyButton title="캘린더에 저장" variant="outline" onPress={saveRecord} />
              </Section>
            )}

            {/* 채팅: 결과가 있으면 노출 */}
            {(res?.nutrition?.[0] && (evalMsg || suggest)) && (
              <Section title="대화형 답변 (데모)">
                <ChatDemo
                  mealName={res!.nutrition[0].name ?? "이번 식사"}
                  score={evalMsg?.score ?? 80}
                  advice={evalMsg?.advice ?? ["이번 끼니 데이터가 부족하지만 전반적으로 무난해요."]}
                  suggestions={suggest ?? [{ title:"다음 끼니 가볍게", reason:"데모 기본 제안", items:["샐러드 + 단백질", "밥 1/2", "소스·당류 줄이기"] }]}
                />
              </Section>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
