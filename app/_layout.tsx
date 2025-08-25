// app/_layout.tsx
import { Inter_400Regular, Inter_600SemiBold, useFonts } from '@expo-google-fonts/inter';
import { NotoSansKR_400Regular, NotoSansKR_700Bold } from '@expo-google-fonts/noto-sans-kr';
import { Stack } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';
import { PaperProvider, Portal } from 'react-native-paper';
import { paperTheme } from '../theme';

export default function RootLayout() {
  const [loaded] = useFonts({
    Inter_400Regular,
    Inter_600SemiBold,
    NotoSansKR_400Regular,
    NotoSansKR_700Bold,
  });

  if (!loaded) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <PaperProvider theme={paperTheme}>
      <Portal.Host>
        {/* /(tabs), /login, /signup 등 파일 기반 라우트 자동 포함 */}
        <Stack screenOptions={{ headerShown: false }} />
      </Portal.Host>
    </PaperProvider>
  );
}
