// app/(tabs)/index.tsx
import { View, Text, Button } from 'react-native';
import { router } from 'expo-router';

export default function HomeScreen() {
  return (
    <View style={{ flex: 1, alignItems:'center', justifyContent:'center', gap: 12 }}>
      <Text>홈 화면</Text>
      <Button title="채팅으로 이동" onPress={() => router.push('/(tabs)/chat')} />
    </View>
  );
}
