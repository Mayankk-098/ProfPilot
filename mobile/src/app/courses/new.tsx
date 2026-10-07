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

import { createCourse } from "../../services/api";

export default function NewCourseScreen() {
  const router = useRouter();

  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [shortName, setShortName] = useState("");
  const [section, setSection] = useState("");
  const [startDate, setStartDate] = useState("");
  const [plannedEndDate, setPlannedEndDate] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate() {
    if (
      !code.trim() ||
      !name.trim() ||
      !shortName.trim() ||
      !section.trim() ||
      !startDate.trim() ||
      !plannedEndDate.trim()
    ) {
      setError("Please complete every field.");
      return;
    }

    if (startDate > plannedEndDate) {
      setError("Planned end date must be after the start date.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      await createCourse({
        code: code.trim().toUpperCase(),
        name: name.trim(),
        short_name: shortName.trim().toUpperCase(),
        section: section.trim(),
        start_date: startDate.trim(),
        planned_end_date: plannedEndDate.trim(),
      });

      router.replace("/courses");
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Couldn't create course."
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

        <Text style={styles.eyebrow}>SETUP · STEP 1</Text>

        <Text style={styles.title}>Create your first course</Text>

        <Text style={styles.subtitle}>
          ProfPilot uses this course as the foundation for syllabus, timetable, roster, attendance, and AI insights.
        </Text>

        <View style={styles.form}>
          <Field
            label="Course Code"
            placeholder="CSE-301"
            value={code}
            onChangeText={setCode}
            autoCapitalize="characters"
          />

          <Field
            label="Course Name"
            placeholder="Operating Systems"
            value={name}
            onChangeText={setName}
          />

          <Field
            label="Short Name"
            placeholder="OS"
            value={shortName}
            onChangeText={setShortName}
            autoCapitalize="characters"
          />

          <Field
            label="Section / Batch"
            placeholder="CSE-A"
            value={section}
            onChangeText={setSection}
          />

          <Field
            label="Semester Start"
            placeholder="YYYY-MM-DD"
            value={startDate}
            onChangeText={setStartDate}
            autoCapitalize="none"
          />

          <Field
            label="Planned End Date"
            placeholder="YYYY-MM-DD"
            value={plannedEndDate}
            onChangeText={setPlannedEndDate}
            autoCapitalize="none"
          />

          {error ? (
            <Text style={styles.error}>{error}</Text>
          ) : null}

          <Pressable
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
            ]}
            onPress={handleCreate}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? "Creating course..." : "Create Course"}
            </Text>
          </Pressable>

          <Pressable
            style={styles.secondary}
            onPress={() => router.replace("/home")}
            disabled={loading}
          >
            <Text style={styles.secondaryText}>
              Skip for now
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
  autoCapitalize = "sentences",
}: {
  label: string;
  placeholder: string;
  value: string;
  onChangeText: (value: string) => void;
  autoCapitalize?: "none" | "sentences" | "characters";
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
    marginBottom: 18,
  },

  back: {
    color: "#FFFFFF",
    fontSize: 38,
    lineHeight: 38,
  },

  eyebrow: {
    color: "#6FC5FF",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1.2,
  },

  title: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "800",
    lineHeight: 34,
    marginTop: 9,
  },

  subtitle: {
    color: "#788391",
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8,
    marginBottom: 28,
  },

  form: {
    marginTop: 2,
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
  },

  buttonPressed: {
    opacity: 0.7,
  },

  buttonText: {
    color: "#0B0D10",
    fontSize: 15,
    fontWeight: "700",
  },

  secondary: {
    alignItems: "center",
    paddingVertical: 14,
  },

  secondaryText: {
    color: "#6FC5FF",
    fontSize: 12,
    fontWeight: "600",
  },
});
