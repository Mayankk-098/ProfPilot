import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useState } from "react";
import { useRouter } from "expo-router";

export default function LoginScreen() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = () => {
    // Demo authentication for now.
    // Real authentication will be connected later.
    if (!email.trim() || !password.trim()) {
      return;
    }

    router.replace("/home");
  };

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.container}>
        <View style={styles.logoContainer}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>P</Text>
          </View>

          <Text style={styles.brand}>ProfPilot</Text>

          <Text style={styles.tagline}>
            Your AI companion for academic life.
          </Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.heading}>Welcome back</Text>

          <Text style={styles.subheading}>
            Sign in to your faculty workspace.
          </Text>

          <Text style={styles.label}>University Email</Text>

          <TextInput
            style={styles.input}
            placeholder="professor@university.edu"
            placeholderTextColor="#68727F"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />

          <Text style={styles.label}>Password</Text>

          <TextInput
            style={styles.input}
            placeholder="Enter your password"
            placeholderTextColor="#68727F"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <Pressable
            style={({ pressed }) => [
              styles.loginButton,
              pressed && styles.pressed,
            ]}
            onPress={handleLogin}
          >
            <Text style={styles.loginText}>Sign In</Text>
          </Pressable>

          <Text style={styles.demoHint}>
            Demo account: enter any email and password
          </Text>
        </View>

        <Text style={styles.footer}>
          ProfPilot · Academic Intelligence Platform
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#0B0D10",
  },

  container: {
    flex: 1,
    justifyContent: "space-between",
    paddingHorizontal: 28,
    paddingTop: 80,
    paddingBottom: 30,
  },

  logoContainer: {
    alignItems: "center",
  },

  logo: {
    width: 70,
    height: 70,
    borderRadius: 20,
    backgroundColor: "#6FC5FF",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 17,
  },

  logoText: {
    color: "#0B0D10",
    fontSize: 34,
    fontWeight: "800",
  },

  brand: {
    color: "#FFFFFF",
    fontSize: 32,
    fontWeight: "800",
  },

  tagline: {
    color: "#77818D",
    fontSize: 14,
    marginTop: 8,
  },

  form: {
    marginTop: 30,
  },

  heading: {
    color: "#FFFFFF",
    fontSize: 26,
    fontWeight: "700",
  },

  subheading: {
    color: "#7A8592",
    fontSize: 14,
    marginTop: 6,
    marginBottom: 30,
  },

  label: {
    color: "#AAB3BE",
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 8,
  },

  input: {
    height: 54,
    backgroundColor: "#171A20",
    borderWidth: 1,
    borderColor: "#252A31",
    borderRadius: 14,
    paddingHorizontal: 16,
    color: "#FFFFFF",
    fontSize: 14,
    marginBottom: 18,
  },

  loginButton: {
    height: 54,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 5,
  },

  pressed: {
    opacity: 0.7,
    transform: [{ scale: 0.98 }],
  },

  loginText: {
    color: "#0B0D10",
    fontWeight: "700",
    fontSize: 15,
  },

  demoHint: {
    color: "#56616D",
    textAlign: "center",
    fontSize: 11,
    marginTop: 14,
  },

  footer: {
    color: "#454E58",
    textAlign: "center",
    fontSize: 11,
  },
});