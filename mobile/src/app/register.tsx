import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useState } from "react";
import { useRouter } from "expo-router";

import { registerLecturer } from "../services/api";

export default function RegisterScreen() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRegister() {
    if (
      !name.trim() ||
      !title.trim() ||
      !department.trim() ||
      !email.trim() ||
      !password.trim()
    ) {
      setError("Please complete every field.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      await registerLecturer({
        name: name.trim(),
        title: title.trim(),
        department: department.trim(),
        email: email.trim(),
        password,
      });

      // A newly registered lecturer starts with an empty workspace.
      // Send them directly into first-course setup.
      router.replace("/courses/new");
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Couldn't create your account."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <Pressable
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Text style={styles.back}>‹</Text>
        </Pressable>

        <View style={styles.brandArea}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>P</Text>
          </View>

          <Text style={styles.brand}>Create your faculty workspace</Text>

          <Text style={styles.subtitle}>
            Set up your ProfPilot account. Your academic data starts empty and belongs to you.
          </Text>
        </View>

        <View style={styles.form}>
          <Field
            label="Full Name"
            placeholder="Dr. Ananya Sharma"
            value={name}
            onChangeText={setName}
          />

          <Field
            label="Academic Title"
            placeholder="Assistant Professor"
            value={title}
            onChangeText={setTitle}
          />

          <Field
            label="Department"
            placeholder="Computer Science & Engineering"
            value={department}
            onChangeText={setDepartment}
          />

          <Field
            label="University Email"
            placeholder="professor@university.edu"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <Field
            label="Password"
            placeholder="At least 8 characters"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          {error ? (
            <Text style={styles.error}>{error}</Text>
          ) : null}

          <Pressable
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
            ]}
            onPress={handleRegister}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? "Creating workspace..." : "Create Account"}
            </Text>
          </Pressable>

          <Pressable
            style={styles.loginLink}
            onPress={() => router.replace("/")}
          >
            <Text style={styles.loginText}>
              Already have an account? Sign in
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function Field({
  label,
  placeholder,
  value,
  onChangeText,
  secureTextEntry = false,
  keyboardType,
  autoCapitalize = "sentences",
}: {
  label: string;
  placeholder: string;
  value: string;
  onChangeText: (value: string) => void;
  secureTextEntry?: boolean;
  keyboardType?: "default" | "email-address";
  autoCapitalize?: "none" | "sentences";
}) {
  return (
    <View>
      <Text style={styles.label}>{label}</Text>

      <TextInput
        style={styles.input}
        placeholder={placeholder}
        placeholderTextColor="#68727F"
        value={value}
        onChangeText={onChangeText}
        secureTextEntry={secureTextEntry}
        keyboardType={keyboardType}
        autoCapitalize={autoCapitalize}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#0B0D10",
  },

  container: {
    padding: 24,
    paddingTop: 58,
    paddingBottom: 35,
  },

  backButton: {
    alignSelf: "flex-start",
    paddingRight: 15,
    paddingVertical: 2,
    marginBottom: 14,
  },

  back: {
    color: "#FFFFFF",
    fontSize: 38,
    lineHeight: 38,
  },

  brandArea: {
    marginBottom: 28,
  },

  logo: {
    width: 54,
    height: 54,
    borderRadius: 16,
    backgroundColor: "#6FC5FF",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },

  logoText: {
    color: "#0B0D10",
    fontSize: 27,
    fontWeight: "800",
  },

  brand: {
    color: "#FFFFFF",
    fontSize: 27,
    fontWeight: "800",
    lineHeight: 33,
  },

  subtitle: {
    color: "#788391",
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8,
  },

  form: {
    marginTop: 4,
  },

  label: {
    color: "#AAB3BE",
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 8,
  },

  input: {
    height: 52,
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
    lineHeight: 18,
    marginBottom: 12,
  },

  button: {
    height: 54,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 2,
  },

  buttonPressed: {
    opacity: 0.7,
  },

  buttonText: {
    color: "#0B0D10",
    fontSize: 15,
    fontWeight: "700",
  },

  loginLink: {
    alignItems: "center",
    marginTop: 18,
    paddingVertical: 8,
  },

  loginText: {
    color: "#6FC5FF",
    fontSize: 12,
    fontWeight: "600",
  },
});
