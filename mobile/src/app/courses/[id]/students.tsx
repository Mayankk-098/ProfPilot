import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";

import {
  CourseDetail,
  Student,
  StudentImportPreviewResponse,
  addCourseStudent,
  confirmStudentImport,
  getCourse,
  getCourseStudents,
  previewStudentImport,
  removeCourseStudent,
  updateStudent,
} from "../../../services/api";

export default function StudentRosterScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const courseId = Array.isArray(id) ? id[0] : id;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [rollNo, setRollNo] = useState("");
  const [name, setName] = useState("");
  const [section, setSection] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);

  const [importOpen, setImportOpen] = useState(false);
  const [csvText, setCsvText] = useState("");
  const [preview, setPreview] = useState<StudentImportPreviewResponse | null>(null);

  const load = useCallback(async () => {
    if (!courseId) {
      setError("Course id is missing.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const [courseData, studentData] = await Promise.all([
        getCourse(courseId),
        getCourseStudents(courseId),
      ]);

      setCourse(courseData);
      setStudents(studentData);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load the student roster."
      );
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    void Promise.resolve().then(() => load());
  }, [load]);

  const filteredStudents = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return students;

    return students.filter(
      (student) =>
        student.roll_no.toLowerCase().includes(query) ||
        student.name.toLowerCase().includes(query) ||
        student.section.toLowerCase().includes(query)
    );
  }, [search, students]);

  function resetForm() {
    setRollNo("");
    setName("");
    setSection("");
    setEditingId(null);
  }

  function beginEdit(student: Student) {
    setEditingId(student.id);
    setRollNo(student.roll_no);
    setName(student.name);
    setSection(student.section);
  }

  async function saveStudent() {
    if (!courseId) return;

    const nextRoll = rollNo.trim();
    const nextName = name.trim();
    const nextSection = section.trim();

    if (!nextRoll || !nextName) {
      setError("Roll number and student name are required.");
      return;
    }

    try {
      setWorking(true);
      setError("");

      if (editingId) {
        await updateStudent(editingId, {
          roll_no: nextRoll,
          name: nextName,
          section: nextSection,
        });
      } else {
        await addCourseStudent(courseId, {
          roll_no: nextRoll,
          name: nextName,
          section: nextSection || null,
        });
      }

      resetForm();
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't save the student."
      );
    } finally {
      setWorking(false);
    }
  }

  function confirmRemove(student: Student) {
    if (!courseId || !course) return;

    Alert.alert(
      "Remove student?",
      student.roll_no + " · " + student.name + " will be unenrolled from " + course.code + ".",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Remove",
          style: "destructive",
          onPress: () =>
            void (async () => {
              try {
                setWorking(true);
                setError("");
                await removeCourseStudent(courseId, student.id);
                if (editingId === student.id) resetForm();
                await load();
              } catch (err) {
                setError(
                  err instanceof Error
                    ? err.message
                    : "Couldn't remove the student."
                );
              } finally {
                setWorking(false);
              }
            })(),
        },
      ]
    );
  }

  async function previewCsv() {
    if (!courseId || !csvText.trim()) {
      setError("Paste CSV content first.");
      return;
    }

    try {
      setWorking(true);
      setError("");
      setPreview(await previewStudentImport(courseId, csvText));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't preview the CSV.");
      setPreview(null);
    } finally {
      setWorking(false);
    }
  }

  async function importValidRows() {
    if (!courseId || !preview) return;

    const rows = preview.rows
      .filter((row) => row.status === "ok")
      .map((row) => ({
        roll_no: row.roll_no,
        name: row.name,
        section: row.section || "",
      }));

    if (rows.length === 0) {
      setError("There are no valid rows to import.");
      return;
    }

    try {
      setWorking(true);
      setError("");
      const result = await confirmStudentImport(courseId, rows);
      setCsvText("");
      setPreview(null);
      setImportOpen(false);
      await load();

      Alert.alert(
        "Import complete",
        result.created + " new students created; " +
          result.enrolled + " enrollments processed."
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't import the students.");
    } finally {
      setWorking(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6FC5FF" />
          <Text style={styles.stateText}>Loading roster...</Text>
        </View>
      </View>
    );
  }

  if (!course) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>Roster unavailable</Text>
          <Text style={styles.errorText}>{error || "Course not found."}</Text>
          <Pressable style={styles.primaryButton} onPress={() => void load()}>
            <Text style={styles.primaryText}>Retry</Text>
          </Pressable>
        </View>
      </View>
    );
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
        <View style={styles.topBar}>
          <Pressable onPress={() => router.back()} style={styles.backButton}>
            <Text style={styles.back}>‹</Text>
          </Pressable>

          <View style={styles.topBarText}>
            <Text style={styles.eyebrow}>COURSE WORKSPACE</Text>
            <Text style={styles.title}>Students</Text>
            <Text style={styles.subtitle}>
              {course.code + " · " + course.section + " · " + students.length + " enrolled"}
            </Text>
          </View>
        </View>

        {error ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        <View style={styles.editorCard}>
          <View style={styles.editorHeader}>
            <View>
              <Text style={styles.sectionLabel}>
                {editingId ? "EDIT STUDENT" : "ADD STUDENT"}
              </Text>
              <Text style={styles.editorTitle}>
                {editingId ? "Update student details" : "Add to roster"}
              </Text>
            </View>

            {editingId ? (
              <Pressable onPress={resetForm} disabled={working}>
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>
            ) : null}
          </View>

          <Text style={styles.label}>Roll number</Text>
          <TextInput
            style={styles.input}
            value={rollNo}
            onChangeText={setRollNo}
            placeholder="24bcs001"
            placeholderTextColor="#68727F"
            autoCapitalize="none"
            editable={!working}
          />

          <Text style={styles.label}>Name</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="Student name"
            placeholderTextColor="#68727F"
            editable={!working}
          />

          <Text style={styles.label}>Section</Text>
          <TextInput
            style={styles.input}
            value={section}
            onChangeText={setSection}
            placeholder={course.section || "A"}
            placeholderTextColor="#68727F"
            editable={!working}
          />

          <Pressable
            style={[styles.primaryButton, working && styles.disabledButton]}
            onPress={() => void saveStudent()}
            disabled={working}
          >
            <Text style={styles.primaryText}>
              {working ? "Saving..." : editingId ? "Save Changes" : "Add Student"}
            </Text>
          </Pressable>
        </View>

        <View style={styles.searchCard}>
          <TextInput
            style={styles.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder="Search roll number, name or section"
            placeholderTextColor="#68727F"
            autoCapitalize="none"
            editable={!working}
          />
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Roster</Text>
          <Text style={styles.countText}>
            {filteredStudents.length}/{students.length}
          </Text>
        </View>

        {filteredStudents.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>
              {students.length === 0 ? "No students enrolled yet" : "No matching students"}
            </Text>
            <Text style={styles.emptyText}>
              {students.length === 0
                ? "Add a student above or use CSV import below."
                : "Try another name, roll number or section."}
            </Text>
          </View>
        ) : (
          filteredStudents.map((student) => (
            <Pressable
              key={student.id}
              style={styles.studentCard}
              onPress={() =>
                router.push({
                  pathname: "/attendance/student as any",
                  params: { course_id: courseId, student_id: student.id },
                })
              }
              disabled={working}
            >
              <View style={styles.studentMain}>
                <Text style={styles.rollNo}>{student.roll_no}</Text>
                <Text style={styles.studentName}>{student.name}</Text>
                {student.section ? (
                  <Text style={styles.sectionMeta}>Section {student.section}</Text>
                ) : null}
              </View>

              <View style={styles.studentActions}>
                <Pressable
                  style={styles.iconButton}
                  onPress={() => beginEdit(student)}
                  disabled={working}
                >
                  <Text style={styles.iconText}>✎</Text>
                </Pressable>

                <Pressable
                  style={styles.iconButton}
                  onPress={() => confirmRemove(student)}
                  disabled={working}
                >
                  <Text style={styles.deleteText}>⌫</Text>
                </Pressable>
              </View>
            </Pressable>
          ))
        )}

        <View style={styles.importHeader}>
          <View style={styles.importHeaderText}>
            <Text style={styles.sectionLabel}>BULK IMPORT</Text>
            <Text style={styles.editorTitle}>Import from CSV</Text>
          </View>

          <Pressable
            style={styles.secondaryButton}
            onPress={() => setImportOpen((value) => !value)}
            disabled={working}
          >
            <Text style={styles.secondaryText}>
              {importOpen ? "Hide" : "Open"}
            </Text>
          </Pressable>
        </View>

        {importOpen ? (
          <View style={styles.importCard}>
            <Text style={styles.importHint}>
              Required: roll_no, name. Optional: section.
            </Text>

            <TextInput
              style={styles.csvInput}
              value={csvText}
              onChangeText={setCsvText}
              placeholder={"roll_no,name,section\n24bcs001,Ananya Sharma,A\n24bcs002,Rahul Singh,A"}
              placeholderTextColor="#68727F"
              multiline
              textAlignVertical="top"
              autoCapitalize="none"
              editable={!working}
            />

            <Pressable
              style={[styles.secondaryAction, working && styles.disabledButton]}
              onPress={() => void previewCsv()}
              disabled={working}
            >
              <Text style={styles.secondaryActionText}>Preview CSV</Text>
            </Pressable>

            {preview ? (
              <View style={styles.previewBox}>
                <View style={styles.previewSummary}>
                  <Text style={styles.previewSummaryText}>
                    {preview.valid_count + " valid · " + preview.error_count + " blocked"}
                  </Text>

                  <Pressable
                    style={[
                      styles.primarySmall,
                      (working || preview.valid_count === 0) && styles.disabledButton,
                    ]}
                    onPress={() => void importValidRows()}
                    disabled={working || preview.valid_count === 0}
                  >
                    <Text style={styles.primarySmallText}>Import valid</Text>
                  </Pressable>
                </View>

                {preview.rows.map((row) => (
                  <View key={row.line} style={styles.previewRow}>
                    <View style={styles.previewRowTop}>
                      <Text style={styles.previewLine}>Line {row.line}</Text>
                      <Text
                        style={[
                          styles.previewStatus,
                          row.status === "ok" ? styles.okStatus : styles.badStatus,
                        ]}
                      >
                        {row.status.toUpperCase()}
                      </Text>
                    </View>

                    <Text style={styles.previewStudent}>
                      {(row.roll_no || "No roll") + " · " + (row.name || "No name")}
                    </Text>
                    <Text style={styles.previewMessage}>{row.message}</Text>
                  </View>
                ))}
              </View>
            ) : null}
          </View>
        ) : null}

        <View style={{ height: 35 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#0B0D10" },
  container: { padding: 20, paddingTop: 55, paddingBottom: 40 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 25 },
  stateText: { color: "#7E8794", marginTop: 12 },
  errorTitle: { color: "#FFFFFF", fontSize: 20, fontWeight: "700" },
  errorText: { color: "#FFB0B0", fontSize: 11, lineHeight: 17 },
  topBar: { flexDirection: "row", alignItems: "center", marginBottom: 24 },
  backButton: { marginRight: 10, paddingRight: 8 },
  back: { color: "#FFFFFF", fontSize: 38, lineHeight: 38 },
  topBarText: { flex: 1 },
  eyebrow: { color: "#6FC5FF", fontSize: 9, fontWeight: "800", letterSpacing: 1.1 },
  title: { color: "#FFFFFF", fontSize: 28, fontWeight: "800", marginTop: 3 },
  subtitle: { color: "#76818D", fontSize: 12, lineHeight: 18, marginTop: 4 },
  errorBanner: {
    backgroundColor: "#2A1B1E", borderWidth: 1, borderColor: "#513036",
    borderRadius: 12, padding: 12, marginBottom: 14,
  },
  editorCard: { backgroundColor: "#171A20", borderRadius: 19, padding: 17, marginBottom: 18 },
  editorHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 15 },
  sectionLabel: { color: "#6FC5FF", fontSize: 9, fontWeight: "800", letterSpacing: 1 },
  editorTitle: { color: "#FFFFFF", fontSize: 16, fontWeight: "700", marginTop: 4 },
  cancelText: { color: "#7D8995", fontSize: 10, fontWeight: "600" },
  label: { color: "#AAB3BE", fontSize: 11, fontWeight: "600", marginBottom: 7 },
  input: {
    height: 48, backgroundColor: "#0F1216", borderWidth: 1, borderColor: "#292F37",
    borderRadius: 12, paddingHorizontal: 13, color: "#FFFFFF", fontSize: 12, marginBottom: 15,
  },
  primaryButton: {
    minHeight: 50, backgroundColor: "#FFFFFF", borderRadius: 12,
    alignItems: "center", justifyContent: "center", marginTop: 3,
  },
  primarySmall: {
    minHeight: 38, backgroundColor: "#FFFFFF", borderRadius: 10,
    paddingHorizontal: 13, alignItems: "center", justifyContent: "center",
  },
  primarySmallText: { color: "#0B0D10", fontSize: 10, fontWeight: "800" },
  primaryText: { color: "#0B0D10", fontSize: 12, fontWeight: "800" },
  disabledButton: { opacity: 0.55 },
  searchCard: { backgroundColor: "#171A20", borderRadius: 15, padding: 10, marginBottom: 22 },
  searchInput: {
    height: 42, backgroundColor: "#0F1216", borderRadius: 10,
    paddingHorizontal: 12, color: "#FFFFFF", fontSize: 11,
  },
  sectionHeader: {
    flexDirection: "row", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12,
  },
  sectionTitle: { color: "#FFFFFF", fontSize: 18, fontWeight: "700" },
  countText: { color: "#65717D", fontSize: 10 },
  emptyCard: {
    backgroundColor: "#171A20", borderRadius: 18, padding: 22,
    alignItems: "center", marginBottom: 18,
  },
  emptyTitle: { color: "#FFFFFF", fontSize: 15, fontWeight: "700", textAlign: "center" },
  emptyText: { color: "#7F8B97", fontSize: 11, lineHeight: 17, textAlign: "center", marginTop: 7 },
  studentCard: {
    backgroundColor: "#171A20", borderRadius: 17, padding: 16, marginBottom: 9,
    flexDirection: "row", alignItems: "center",
  },
  studentMain: { flex: 1, paddingRight: 10 },
  rollNo: { color: "#FFFFFF", fontSize: 14, fontWeight: "800" },
  studentName: { color: "#B2BAC4", fontSize: 12, marginTop: 4 },
  sectionMeta: { color: "#68747F", fontSize: 10, marginTop: 5 },
  studentActions: { flexDirection: "row", gap: 5 },
  iconButton: {
    width: 30, height: 30, borderRadius: 8, backgroundColor: "#252C34",
    alignItems: "center", justifyContent: "center",
  },
  iconText: { color: "#CDD4DB", fontSize: 11, fontWeight: "700" },
  deleteText: { color: "#FF9B9B", fontSize: 11, fontWeight: "700" },
  importHeader: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    marginTop: 21, marginBottom: 10,
  },
  importHeaderText: { flex: 1 },
  secondaryButton: {
    borderWidth: 1, borderColor: "#303842", backgroundColor: "#14181D",
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, marginLeft: 12,
  },
  secondaryText: { color: "#C3CBD3", fontSize: 10, fontWeight: "700" },
  importCard: { backgroundColor: "#171A20", borderRadius: 18, padding: 16 },
  importHint: { color: "#7D8995", fontSize: 10, lineHeight: 16, marginBottom: 10 },
  csvInput: {
    minHeight: 150, backgroundColor: "#0F1216", borderWidth: 1, borderColor: "#292F37",
    borderRadius: 12, paddingHorizontal: 12, paddingVertical: 12,
    color: "#FFFFFF", fontSize: 11, lineHeight: 17,
  },
  secondaryAction: {
    minHeight: 46, borderRadius: 11, borderWidth: 1, borderColor: "#3A4651",
    alignItems: "center", justifyContent: "center", marginTop: 11,
  },
  secondaryActionText: { color: "#D7DEE5", fontSize: 11, fontWeight: "800" },
  previewBox: { marginTop: 14, borderTopWidth: 1, borderTopColor: "#252C33", paddingTop: 14 },
  previewSummary: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 9,
  },
  previewSummaryText: { color: "#C9D0D8", fontSize: 10, fontWeight: "700" },
  previewRow: { backgroundColor: "#11151A", borderRadius: 11, padding: 11, marginTop: 7 },
  previewRowTop: { flexDirection: "row", justifyContent: "space-between" },
  previewLine: { color: "#697580", fontSize: 9 },
  previewStatus: { fontSize: 9, fontWeight: "800" },
  okStatus: { color: "#72D6A0" },
  badStatus: { color: "#FF9B9B" },
  previewStudent: { color: "#D9E0E7", fontSize: 11, fontWeight: "700", marginTop: 5 },
  previewMessage: { color: "#75818D", fontSize: 9, lineHeight: 14, marginTop: 4 },
});
