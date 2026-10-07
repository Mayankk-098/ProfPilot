import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  useState,
} from "react";

import {
  useRouter,
} from "expo-router";

import {
  login,
} from "../services/api";

export default function LoginScreen() {
  const router =
    useRouter();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleLogin() {
    if (
      !email.trim() ||
      !password.trim()
    ) {
      setError(
        "Please enter email and password."
      );

      return;
    }

    try {
      setLoading(true);
      setError("");

      await login(
        email.trim(),
        password
      );

      router.replace("/home" as any);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Login failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={
        Platform.OS === "ios"
          ? "padding"
          : undefined
      }
    >
      <View style={styles.container}>
        <View style={styles.brandArea}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>
              P
            </Text>
          </View>

          <Text style={styles.brand}>
            ProfPilot
          </Text>

          <Text style={styles.tagline}>
            Your AI companion for academic life.
          </Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.heading}>
            Welcome back
          </Text>

          <Text style={styles.subheading}>
            Sign in to your faculty workspace.
          </Text>

          <Text style={styles.label}>
            University Email
          </Text>

          <TextInput
            style={styles.input}
            placeholder="professor@university.edu"
            placeholderTextColor="#68727F"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />

          <Text style={styles.label}>
            Password
          </Text>

          <TextInput
            style={styles.input}
            placeholder="Enter your password"
            placeholderTextColor="#68727F"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          {error ? (
            <Text style={styles.error}>
              {error}
            </Text>
          ) : null}

          <Pressable
            style={({ pressed }) => [
              styles.button,
              pressed &&
                styles.buttonPressed,
            ]}
            onPress={handleLogin}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading
                ? "Signing in..."
                : "Sign In"}
            </Text>
          </Pressable>

          <Text style={styles.hint}>
            Sign in using your faculty account.
          </Text>

          <Pressable
            style={styles.signupButton}
            onPress={() => router.push("/register" as any)}
          >
            <Text style={styles.signupText}>
              Create faculty account
            </Text>
          </Pressable>
        </View>

        <Text style={styles.footer}>
          ProfPilot · Academic Intelligence Platform
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles =
  StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: "#0B0D10",
    },

    container: {
      flex: 1,
      justifyContent: "space-between",
      padding: 28,
      paddingTop: 80,
      paddingBottom: 30,
    },

    brandArea: {
      alignItems: "center",
    },

    logo: {
      width: 70,
      height: 70,
      borderRadius: 20,
      backgroundColor: "#6FC5FF",
      alignItems: "center",
      justifyContent: "center",
      marginBottom: 16,
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

    error: {
      color: "#FF9B9B",
      fontSize: 12,
      marginBottom: 12,
    },

    button: {
      height: 54,
      backgroundColor: "#FFFFFF",
      borderRadius: 14,
      alignItems: "center",
      justifyContent: "center",
    },

    buttonPressed: {
      opacity: 0.7,
    },

    buttonText: {
      color: "#0B0D10",
      fontSize: 15,
      fontWeight: "700",
    },

    hint: {
      color: "#56616D",
      textAlign: "center",
      fontSize: 11,
      marginTop: 14,
    },

    signupButton: {
      marginTop: 18,
      alignItems: "center",
      paddingVertical: 10,
    },

    signupText: {
      color: "#6FC5FF",
      fontSize: 13,
      fontWeight: "700",
    },

    footer: {
      color: "#454E58",
      textAlign: "center",
      fontSize: 11,
    },
  });