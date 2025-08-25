// app/(tabs)/chat.tsx
import { View, Text } from 'react-native';
import { Stack } from 'expo-router';

export default function ChatScreen() {
  return (
    <>
      <Stack.Screen options={{ title: 'Chat' }} />
      <View style={{ flex: 1, alignItems:'center', justifyContent:'center' }}>
        <Text>Chat screen</Text>
      </View>
    </>
  );
}
