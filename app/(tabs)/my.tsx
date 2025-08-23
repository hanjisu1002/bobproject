// app/(tabs)/my.tsx
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { useFocusEffect } from "@react-navigation/native";
import { useRouter } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ScrollView, View } from "react-native";
import { Button, Card, Chip, Dialog, Divider, Portal, Text } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";

import MacroDialog from "../../components/MacroDialog";
import MultiSelectDialog from "../../components/MultiSelectDialog";
import RingProgress from "../../components/RingProgress";
import TargetKcalDialog from "../../components/TargetKcalDialog";

import { authAPI, menuAPI, userAPI } from "../../lib/api"; // Import menuAPI
import { getTodaySummary } from "../../lib/records";
import { loadJSON, saveJSON } from "../../lib/storage";
import type { Profile } from "../../lib/types";
import { palette, radius, space } from "../../theme";

const ALLERGEN_OPTIONS = ["계란", "우유", "땅콩", "대두", "밀", "갑각류", "생선", "돼지고기", "소고기"];

export default function My() {
  const router = useRouter();
  const tabH = useBottomTabBarHeight();

  const [token, setToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [today, setToday] = useState<{ totalKcal: number; items: any[] } | null>(null);

  // 다이얼로그 on/off
  const [openMacro, setOpenMacro] = useState(false);
  const [openPref, setOpenPref] = useState(false);
  const [openAller, setOpenAller] = useState(false);
  const [openTarget, setOpenTarget] = useState(false);
  const [deleteConfirmVisible, setDeleteConfirmVisible] = useState(false);

  // 버튼 로딩 상태
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [categories, setCategories] = useState<string[]>([]); // New state for dynamic categories

  // New useEffect to fetch categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await menuAPI.getMenuCategories();
        setCategories(response.data);
      } catch (error) {
        console.error("Failed to fetch categories:", error);
        setCategories([]); // Fallback to empty array if fetch fails
      }
    };
    fetchCategories();
  }, []); // Run once on mount

  const reload = useCallback(async () => {
    const t = await loadJSON<string | null>("token", null);
    if (!t) {
      setToken(null);
      setProfile(null);
      return;
    }

    try {
      const profileRes = await userAPI.getProfile();
      const p = profileRes.data;

      setToken(t);
      setProfile(p);
      await saveJSON("profile", p);

      const s = await getTodaySummary();
      setToday({ totalKcal: s.totalKcal, items: s.items });

    } catch (error: any) {
      if (error.response && error.response.status === 401) {
        console.log("세션 만료, 자동 로그아웃 처리");
        await saveJSON("token", null);
        await saveJSON("profile", null);
        setToken(null);
        setProfile(null);
        router.replace("/login");
      } else {
        console.error("프로필 로딩 에러:", error);
      }
    }
  }, [router]);

  useEffect(() => { reload(); }, [reload]);
  useFocusEffect(useCallback(() => { reload(); }, [reload]));

  // 진행률 (0~1)
  const progress = useMemo(() => {
    const tgt = profile?.daily_kcal_goal ?? 0; // Updated field name
    const cur = today?.totalKcal ?? 0;
    if (!tgt) return 0;
    const r = cur / tgt;
    return r < 0 ? 0 : r > 1 ? 1 : r;
  }, [profile?.daily_kcal_goal, today?.totalKcal]); // Updated field name

  // 저장 핸들러
  const patchProfile = async (next: Profile) => {
    setLoading(true); // Set loading state
    try {
      // Prepare data for backend API call
      const updateData: any = {
        sex: next.sex,
        age: next.age,
        daily_kcal_goal: next.daily_kcal_goal,
        macro_ratio: next.macro_ratio,
        activity_level: next.activity_level,
        exclude_allergens: next.exclude_allergens,
        diet_types: next.diet_types,
        like_cuisines: next.like_cuisines,
        dislike_items: next.dislike_items,
      };
      // Filter out undefined values
      Object.keys(updateData).forEach(key => updateData[key] === undefined && delete updateData[key]);

      const response = await userAPI.updateProfile(updateData);
      const updatedProfile = response.data; // Backend returns the updated profile

      setProfile(updatedProfile); // Update local state with data from backend
      await saveJSON("profile", updatedProfile); // Save to local storage
    } catch (error) {
      console.error("프로필 업데이트 실패:", error);
      // Optionally, revert local state or show error message
    } finally {
      setLoading(false); // Reset loading state
    }
  };

  const onSaveMacro = async (m: { carb: number; protein: number; fat: number }) => {
    if (!profile) return;
    patchProfile({ ...profile, macro_ratio: m }); // Updated field name
  };
  const onSavePrefers = async (arr: string[]) => profile && patchProfile({ ...profile, like_cuisines: arr }); // Updated field name
  const onSaveAllergens = async (arr: string[]) => profile && patchProfile({ ...profile, exclude_allergens: arr }); // Updated field name
  const onSaveTarget = async (kcal: number) => profile && patchProfile({ ...profile, daily_kcal_goal: kcal }); // Updated field name

  // 로그아웃 함수
  const onLogout = async () => {
    setLoading(true);
    try {
      await authAPI.logout();
    } catch (error) {
      console.error("로그아웃 API 에러:", error);
    } finally {
      await saveJSON("token", null);
      await saveJSON("profile", null);
      setLoading(false);
      router.replace("/login");
    }
  };

  // 계정 삭제 함수
  const onDeleteAccount = () => {
    setDeleteConfirmVisible(true);
  };

  const handleDeleteConfirm = async () => {
    setDeleteConfirmVisible(false);
    setDeleting(true);
    try {
      await userAPI.deleteMe();
    } catch (error) {
      console.error("계정 삭제 API 에러:", error);
    } finally {
      await saveJSON("token", null);
      await saveJSON("profile", null);
      setDeleting(false);
      router.replace("/login");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: palette.bg }}>
      {/* 전체 스크롤 가능 + 탭바 패딩 */}
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{
          padding: space(2),
          gap: space(2),
          paddingBottom: tabH + 24,
        }}
      >
        <Text style={{ fontSize: 22, fontWeight: "800" }}>마이페이지</Text>

        {/* 상태 카드 */}
        <Card style={{ borderRadius: radius.lg, overflow: "hidden", backgroundColor: palette.card }}>
          <Card.Content style={{ gap: 10 }}>
            {token && profile ? (
              <>
                <View style={{ gap: 2 }}>
                  <Text style={{ fontSize: 16, fontWeight: "700" }}>
                    {profile.name ?? profile.email?.split("@")[0]} 님 {/* Display name */}
                  </Text>
                  <Text style={{ color: "#6B7280" }}>
                    목표 {profile.daily_kcal_goal ?? "-"} kcal • 탄수화물 {Math.round(profile.macro_ratio?.carb_g ?? 50)}g / 단백질 {Math.round(profile.macro_ratio?.protein_g ?? 25)}g / 지방 {Math.round(profile.macro_ratio?.fat_g ?? 25)}g {/* Updated field names */}
                  </Text>
                </View>

                {/* 목표 달성 현황 */}
                <View style={{ alignItems: "center", marginTop: 4 }}>
                  <Text style={{ fontWeight: "700", marginBottom: 8 }}>오늘 목표 달성 현황</Text>
                  <View style={{ position: 'relative', alignItems: 'center', justifyContent: 'center' }}>
                    <RingProgress size={140} strokeWidth={12} progress={progress} color={palette.primary} />
                    <Text style={{ position: 'absolute', fontSize: 24, fontWeight: 'bold' }}>
                      {`${Math.round(progress * 100)}%`}
                    </Text>
                  </View>
                  <Text style={{ marginTop: 6 }}>
                    {(today?.totalKcal ?? 0)} / {(profile?.daily_kcal_goal ?? "-")} kcal {/* Updated field name */}
                  </Text>
                  <Button
                    mode="outlined"
                    style={{ marginTop: 8 }}
                    onPress={() => setOpenTarget(true)}
                  >
                    오늘 목표 수정
                  </Button>
                </View>

                <Divider style={{ marginVertical: 8 }} />

                {/* 선호/알레르기 — 긴 경우도 줄바꿈 */}
                <View style={{ gap: 8 }}>
                  <Text>선호 카테고리</Text>
                  <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
                    {(profile.like_cuisines ?? []).length // Updated field name
                      ? (profile.like_cuisines ?? []).map((p, i) => ( // Updated field name
                        <Chip
                          key={p + i}
                          compact
                          style={{ backgroundColor: palette.primary }} // Explicitly set background
                          textStyle={{ color: 'white' }} // Explicitly set text color for contrast
                        >
                          {p}
                        </Chip>
                      ))
                      : <Text style={{ color: "#6B7280" }}>없음</Text>}
                  </View>

                  <Text style={{ marginTop: 4 }}>알레르기</Text>
                  <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
                    {(profile.exclude_allergens ?? []).length // Updated field name
                      ? (profile.exclude_allergens ?? []).map((a, i) => ( // Updated field name
                        <Chip
                          key={a + i}
                          compact
                          style={{ backgroundColor: palette.primary }} // Explicitly set background
                          textStyle={{ color: 'white' }} // Explicitly set text color for contrast
                        >
                          {a}
                        </Chip>
                      ))
                      : <Text style={{ color: "#6B7280" }}>없음</Text>}
                  </View>
                </View>

                <Divider style={{ marginVertical: 8 }} />

                <Text style={{ fontWeight: "700" }}>오늘 요약</Text>
                <Text>섭취 합계: {today?.totalKcal ?? 0} kcal (기록 {today?.items.length ?? 0}건)</Text>


                {/* 액션 버튼: 줄바꿈 허용 */}
                <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
                  <Button mode="contained" onPress={() => setOpenMacro(true)}>비율 수정</Button>
                  <Button mode="outlined" onPress={() => setOpenPref(true)}>선호 수정</Button>
                  <Button mode="outlined" onPress={() => setOpenAller(true)}>알레르기 수정</Button>
                  <Button mode="outlined" onPress={onLogout} loading={loading} disabled={loading || deleting}>로그아웃</Button>
                  <Button mode="outlined" onPress={onDeleteAccount} loading={deleting} disabled={loading || deleting} textColor={palette.danger}>계정 삭제</Button>
                </View>
              </>
            ) : (
              <>
                <Text style={{ marginBottom: 8 }}>로그인이 필요해요.</Text>
                <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
                  <Button mode="contained" onPress={() => router.push("/login")}>로그인</Button>
                  <Button mode="outlined" onPress={() => router.push("/signup")}>회원가입</Button>
                </View>
              </>
            )}
          </Card.Content>
        </Card>

        {/* 빠른 메뉴 카드 */}
        {token && profile && (
          <Card style={{ borderRadius: radius.lg, overflow: "hidden", backgroundColor: palette.card }}>
            <Card.Content style={{ gap: 8 }}>
              <Text style={{ fontWeight: "700" }}>빠른 메뉴</Text>
              <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
                <Button mode="outlined" onPress={() => router.push("/upload")}>사진 업로드</Button>
                <Button mode="outlined" onPress={() => router.push("/calendar")}>식단 기록</Button>
              </View>
            </Card.Content>
          </Card>
        )}
      </ScrollView>

      {/* 다이얼로그들 */}
      <Portal>
        <Dialog visible={deleteConfirmVisible} onDismiss={() => setDeleteConfirmVisible(false)} style={{ borderRadius: 0 }}>
          <Dialog.Title>계정 삭제</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium">정말로 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.</Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteConfirmVisible(false)}>취소</Button>
            <Button onPress={handleDeleteConfirm} textColor={palette.danger}>삭제</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <TargetKcalDialog
        open={openTarget}
        initial={profile?.daily_kcal_goal} // Updated field name
        onClose={() => setOpenTarget(false)}
        onSave={onSaveTarget}
      />
      <MacroDialog
        open={openMacro}
        initial={(() => {
          const defaultMacro = { carb: 50, protein: 25, fat: 25 } // 기본 백분율

          if (!profile?.macro_ratio || !profile.daily_kcal_goal) {
            return defaultMacro
          }

          const { carb_g, protein_g, fat_g } = profile.macro_ratio
          const totalKcal = profile.daily_kcal_goal

          const carbKcal = (carb_g ?? 0) * 4
          const proteinKcal = (protein_g ?? 0) * 4
          const fatKcal = (fat_g ?? 0) * 9
          const totalMacroKcal = carbKcal + proteinKcal + fatKcal

          if (totalMacroKcal === 0) {
            return defaultMacro // 0으로 나누는 것을 방지
          }

          const carbPercent = Math.round((carbKcal / totalMacroKcal) * 100)
          const proteinPercent = Math.round((proteinKcal / totalMacroKcal) * 100)
          let fatPercent = 100 - carbPercent - proteinPercent // 합계 100으로 조정

          return {
            carb: carbPercent,
            protein: proteinPercent,
            fat: fatPercent,
          }
        })()}
        onClose={() => setOpenMacro(false)}
        onSave={onSaveMacro}
      />

      <MultiSelectDialog
        title="선호 카테고리"
        options={categories} // Use dynamic categories
        initial={profile?.like_cuisines ?? []} // Updated field name
        open={openPref}
        onClose={() => setOpenPref(false)}
        onSave={onSavePrefers}
      />
      <MultiSelectDialog
        title="알레르기"
        options={ALLERGEN_OPTIONS}
        initial={profile?.exclude_allergens ?? []} // Updated field name
        open={openAller}
        onClose={() => setOpenAller(false)}
        onSave={onSaveAllergens}
      />
    </SafeAreaView>
  );
}