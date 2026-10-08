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
  AttendanceCourseResponse,
  AttendanceSessionResponse,
  AttendanceStatus,
  AttendanceStudent,
  correctAttendance,
  getAcademicContext,
  getAttendanceSession,
  getCourseAttendance,
  getMe,
  submitAttendance,
} from "../services/api";

function todayLocal() {
  const value = new Date();
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return year + "-" + month + "-" + day;
}

export default function AttendanceScreen() {
  const router = useRouter();
  const { course_id, class_date } = useLocalSearchParams<{
    course_id?: string;
    class_date?: string;
  }>();

  const [courseId, setCourseId] = useState<string | null>(
    Array.isArray(course_id) ? course_id[0] : course_id || null
  );
  const [attendance, setAttendance] =
    useState<AttendanceCourseResponse | null>(null);
  const [session, setSession] =
    useState<AttendanceSessionResponse | null>(null);
  const [classDate, setClassDate] = useState(
    Array.isArray(class_date) ? class_date[0] : class_date || todayLocal()
  );
  const [marks, setMarks] =
    useState<Record<string, AttendanceStatus>>({});
  const [loading, setLoading] = useState(true);
  const [sessionLoading, setSessionLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const loadAttendance = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      let selectedCourseId = courseId;

      if (!selectedCourseId) {
        const me = await getMe();
        const context = await getAcademicContext(me.lecturer_id);
        selectedCourseId =
          context.selected_course?.id || context.courses[0]?.id || null;
      }

      if (!selectedCourseId) {
        throw new Error("No course is available for attendance.");
      }

      setCourseId(selectedCourseId);
      setAttendance(await getCourseAttendance(selectedCourseId));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't load attendance."
      );
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    void Promise.resolve().then(() => loadAttendance());
  }, [loadAttendance]);

  async function loadSession() {
    if (!courseId) return;

    if (!/^\d{4}-\d{2}-\d{2}$/.test(classDate.trim())) {
      setError("Use date format YYYY-MM-DD.");
      return;
    }

    try {
      setSessionLoading(true);
      setWorking(false);
      setError("");

      const data = await getAttendanceSession(courseId, classDate.trim());
      setSession(data);

      const nextMarks: Record<string, AttendanceStatus> = {};

      if (data.recorded) {
        for (const record of data.records) {
          nextMarks[record.student_id] = record.status;
        }
      } else {
        for (const student of attendance?.students || []) {
          nextMarks[student.student_id] = "present";
        }
      }

      setMarks(nextMarks);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load this attendance session."
      );
    } finally {
      setSessionLoading(false);
    }
  }

  function setAll(status: AttendanceStatus) {
    const next: Record<string, AttendanceStatus> = {};
    for (const student of attendance?.students || []) {
      next[student.student_id] = status;
    }
    setMarks(next);
  }

  function setStudentStatus(studentId: string, status: AttendanceStatus) {
    setMarks((previous) => ({
      ...previous,
      [studentId]: status,
    }));
  }

  const markedCount = useMemo(
    () =>
      (attendance?.students || []).filter(
        (student) => marks[student.student_id]
      ).length,
    [attendance?.students, marks]
  );

  const presentCount = useMemo(
    () =>
      (attendance?.students || []).filter(
        (student) => marks[student.student_id] === "present"
      ).length,
    [attendance?.students, marks]
  );

  const absentCount = useMemo(
    () =>
      (attendance?.students || []).filter(
        (student) => marks[student.student_id] === "absent"
      ).length,
    [attendance?.students, marks]
  );

  const excusedCount = useMemo(
    () =>
      (attendance?.students || []).filter(
        (student) => marks[student.student_id] === "excused"
      ).length,
    [attendance?.students, marks]
  );

  async function saveSession() {
    if (!courseId || !attendance) return;

    const records = attendance.students.map((student) => ({
      student_id: student.student_id,
      status: marks[student.student_id] || "present",
    }));

    try {
      setWorking(true);
      setError("");

      if (session?.recorded) {
        await correctAttendance(courseId, classDate.trim(), records);
      } else {
        await submitAttendance(courseId, classDate.trim(), records);
      }

      await Promise.all([loadAttendance(), loadSession()]);

      Alert.alert(
        session?.recorded ? "Attendance corrected" : "Attendance recorded",
        presentCount +
          " present · " +
          absentCount +
          " absent · " +
          excusedCount +
          " excused"
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't save attendance."
      );
    } finally {
      setWorking(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6FC5FF" />
          <Text style={styles.stateText}>Loading attendance...</Text>
        </View>
      </View>
    );
  }

  if (error && !attendance) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>Attendance unavailable</Text>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable style={styles.primaryButton} onPress={() => void loadAttendance()}>
            <Text style={styles.primaryText}>Retry</Text>
          </Pressable>
          <Pressable style={styles.backLink} onPress={() => router.back()}>
            <Text style={styles.backLinkText}>Go back</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  if (!attendance) return null;

  const flaggedStudents = attendance.students.filter(
    (student) => student.flagged
  );

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
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>‹</Text>
        </Pressable>

        <Text style={styles.eyebrow}>COURSE WORKSPACE</Text>
        <Text style={styles.title}>Attendance</Text>
        <Text style={styles.subtitle}>
          {attendance.course_code} · {attendance.section}
        </Text>

        {error ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorBannerText}>{error}</Text>
          </View>
        ) : null}

        <View style={styles.sessionCard}>
          <View style={styles.sessionHeader}>
            <View style={styles.sessionHeaderText}>
              <Text style={styles.sectionLabel}>CLASS SESSION</Text>
              <Text style={styles.sessionTitle}>
                {session?.recorded ? "Correct attendance" : "Take attendance"}
              </Text>
            </View>
            {session?.recorded ? (
              <View style={styles.recordedBadge}>
                <Text style={styles.recordedText}>RECORDED</Text>
              </View>
            ) : null}
          </View>

          <Text style={styles.label}>Class date</Text>
          <View style={styles.dateRow}>
            <TextInput
              style={styles.dateInput}
              value={classDate}
              onChangeText={setClassDate}
              placeholder="2026-10-07"
              placeholderTextColor="#68727F"
              autoCapitalize="none"
              editable={!working && !sessionLoading}
            />
            <Pressable
              style={styles.loadButton}
              onPress={() => void loadSession()}
              disabled={working || sessionLoading}
            >
              <Text style={styles.loadButtonText}>
                {sessionLoading ? "Loading" : "Load"}
              </Text>
            </Pressable>
          </View>

          <Text style={styles.helperText}>
            The date must be an active scheduled class for this course.
          </Text>

          {session ? (
            <>
              <View style={styles.sessionSummary}>
                <Text style={styles.summaryStat}>
                  {markedCount}/{attendance.students.length} marked
                </Text>
                <Text style={styles.summaryStat}>
                  {presentCount} present
                </Text>
                <Text style={styles.summaryStat}>
                  {absentCount} absent
                </Text>
                {excusedCount > 0 ? (
                  <Text style={styles.summaryStat}>
                    {excusedCount} excused
                  </Text>
                ) : null}
              </View>

              <View style={styles.quickRow}>
                <Pressable
                  style={styles.quickButton}
                  onPress={() => setAll("present")}
                  disabled={working}
                >
                  <Text style={styles.quickText}>All present</Text>
                </Pressable>

                <Pressable
                  style={styles.quickButton}
                  onPress={() => setAll("absent")}
                  disabled={working}
                >
                  <Text style={styles.quickText}>All absent</Text>
                </Pressable>
              </View>

              {attendance.students.map((student) => (
                <AttendanceRow
                  key={student.student_id}
                  student={student}
                  status={marks[student.student_id] || "present"}
                  disabled={working}
                  onChange={(status) =>
                    setStudentStatus(student.student_id, status)
                  }
                />
              ))}

              <Pressable
                style={[
                  styles.primaryButton,
                  working && styles.disabledButton,
                ]}
                onPress={() => void saveSession()}
                disabled={working}
              >
                <Text style={styles.primaryText}>
                  {working
                    ? "Saving..."
                    : session.recorded
                      ? "Save Correction"
                      : "Save Attendance"}
                </Text>
              </Pressable>
            </>
          ) : (
            <View style={styles.loadHint}>
              <Text style={styles.loadHintTitle}>Ready to mark the roster</Text>
              <Text style={styles.loadHintText}>
                Load a scheduled class date. New sessions start with every
                student marked present so you only need to change absences.
              </Text>
            </View>
          )}
        </View>

        <Text style={styles.sectionTitle}>Attendance health</Text>

        <Pressable
          style={styles.historyButton}
          onPress={() =>
            router.push({
              pathname: "/attendance/history" as any,
              params: { course_id: attendance.course_id },
            })
          }
        >
          <Text style={styles.historyButtonText}>View Attendance History</Text>
        </Pressable>

        <View style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>Class average</Text>
          <Text style={styles.percentage}>
            {attendance.class_average_pct == null
              ? "--"
              : Math.round(attendance.class_average_pct) + "%"}
          </Text>
          <Text style={styles.summaryText}>
            {attendance.present_last_class} present ·{" "}
            {attendance.absent_last_class} absent
          </Text>
          <Text style={styles.classesHeld}>
            {attendance.classes_held} classes held
          </Text>
        </View>

        <Text style={styles.sectionTitle}>
          Students below {attendance.threshold_pct}%
        </Text>

        {flaggedStudents.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>All students are on track</Text>
            <Text style={styles.emptyText}>
              No students are currently below the attendance threshold.
            </Text>
          </View>
        ) : (
          flaggedStudents.map((student) => (
            <StudentCard
              key={student.student_id}
              student={student}
              courseId={attendance.course_id}
            />
          ))
        )}

        <View style={{ height: 60 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function AttendanceRow({
  student,
  status,
  disabled,
  onChange,
}: {
  student: AttendanceStudent;
  status: AttendanceStatus;
  disabled: boolean;
  onChange: (status: AttendanceStatus) => void;
}) {
  return (
    <View style={styles.attendanceRow}>
      <View style={styles.studentInfo}>
        <Text style={styles.rollNo}>{student.roll_no}</Text>
        <Text style={styles.studentName}>{student.name}</Text>
      </View>

      <View style={styles.statusRow}>
        {(["present", "absent", "excused"] as AttendanceStatus[]).map(
          (value) => (
            <Pressable
              key={value}
              style={[
                styles.statusButton,
                status === value && styles.statusButtonActive,
              ]}
              onPress={() => onChange(value)}
              disabled={disabled}
            >
              <Text
                style={[
                  styles.statusText,
                  status === value && styles.statusTextActive,
                ]}
              >
                {value === "present"
                  ? "P"
                  : value === "absent"
                    ? "A"
                    : "E"}
              </Text>
            </Pressable>
          )
        )}
      </View>
    </View>
  );
}

function StudentCard({
  student,
  courseId,
}: {
  student: AttendanceStudent;
  courseId: string;
}) {
  const router = useRouter();
  const percentage =
    student.percentage == null ? null : Math.round(student.percentage);

  return (
    <Pressable
      style={styles.studentCard}
      onPress={() =>
        router.push({
          pathname: "/attendance/student" as any,
          params: {
            course_id: courseId,
            student_id: student.student_id,
          },
        })
      }
    >
      <View style={styles.studentInfo}>
        <Text style={styles.rollNo}>{student.roll_no}</Text>
        <Text style={styles.studentName}>{student.name}</Text>
        <View style={styles.warningBadge}>
          <View style={styles.warningDot} />
          <Text style={styles.warningText}>Below 75%</Text>
        </View>
        <Text style={styles.recoveryText}>
          Needs {student.classes_needed_to_recover} consecutive{" "}
          {student.classes_needed_to_recover === 1 ? "class" : "classes"} to recover
        </Text>
      </View>

      <View style={styles.percentageBox}>
        <Text style={styles.studentPercentage}>
          {percentage == null ? "--" : percentage + "%"}
        </Text>
        <Text style={styles.attendedText}>
          {student.attended}/{student.total}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#0B0D10" },
  container: { padding: 20, paddingTop: 55, paddingBottom: 35 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 25 },
  stateText: { color: "#7E8794", marginTop: 12 },
  backButton: { alignSelf: "flex-start", paddingRight: 15 },
  back: { color: "#FFFFFF", fontSize: 38, lineHeight: 38 },
  eyebrow: { color: "#6FC5FF", fontSize: 9, fontWeight: "800", letterSpacing: 1.1 },
  title: { color: "#FFFFFF", fontSize: 28, fontWeight: "800", marginTop: 5 },
  subtitle: { color: "#7E8794", fontSize: 13, marginTop: 5, marginBottom: 20 },
  errorBanner: {
    backgroundColor: "#2A1B1E", borderWidth: 1, borderColor: "#513036",
    borderRadius: 12, padding: 12, marginBottom: 14,
  },
  errorBannerText: { color: "#FFB0B0", fontSize: 11, lineHeight: 17 },
  sessionCard: { backgroundColor: "#171A20", borderRadius: 20, padding: 17, marginBottom: 25 },
  sessionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 15 },
  sessionHeaderText: { flex: 1 },
  sectionLabel: { color: "#6FC5FF", fontSize: 9, fontWeight: "800", letterSpacing: 1 },
  sessionTitle: { color: "#FFFFFF", fontSize: 17, fontWeight: "700", marginTop: 4 },
  recordedBadge: { backgroundColor: "#1B3025", borderRadius: 8, paddingHorizontal: 8, paddingVertical: 5, marginLeft: 8 },
  recordedText: { color: "#72D6A0", fontSize: 8, fontWeight: "800" },
  label: { color: "#AAB3BE", fontSize: 11, fontWeight: "600", marginBottom: 7 },
  dateRow: { flexDirection: "row", gap: 8 },
  dateInput: {
    flex: 1, height: 46, backgroundColor: "#0F1216", borderWidth: 1,
    borderColor: "#292F37", borderRadius: 11, paddingHorizontal: 12,
    color: "#FFFFFF", fontSize: 12,
  },
  loadButton: {
    width: 72, backgroundColor: "#252E37", borderRadius: 11,
    alignItems: "center", justifyContent: "center",
  },
  loadButtonText: { color: "#DCE3E9", fontSize: 11, fontWeight: "800" },
  helperText: { color: "#66727E", fontSize: 9, lineHeight: 14, marginTop: 7 },
  sessionSummary: {
    flexDirection: "row", flexWrap: "wrap", gap: 8,
    marginTop: 17, marginBottom: 12,
  },
  summaryStat: { color: "#AEB7C0", fontSize: 9, fontWeight: "700" },
  quickRow: { flexDirection: "row", gap: 8, marginBottom: 13 },
  quickButton: {
    flex: 1, minHeight: 38, borderRadius: 10, borderWidth: 1,
    borderColor: "#303842", alignItems: "center", justifyContent: "center",
  },
  quickText: { color: "#C8D0D8", fontSize: 10, fontWeight: "800" },
  attendanceRow: {
    backgroundColor: "#101419", borderRadius: 13, padding: 11,
    marginBottom: 7, flexDirection: "row", alignItems: "center",
  },
  studentInfo: { flex: 1, paddingRight: 8 },
  rollNo: { color: "#FFFFFF", fontSize: 12, fontWeight: "800" },
  studentName: { color: "#8F9AA5", fontSize: 10, marginTop: 3 },
  statusRow: { flexDirection: "row", gap: 5 },
  statusButton: {
    width: 31, height: 31, borderRadius: 8, backgroundColor: "#20262D",
    alignItems: "center", justifyContent: "center",
  },
  statusButtonActive: { backgroundColor: "#344B5A", borderWidth: 1, borderColor: "#6FC5FF" },
  statusText: { color: "#68737F", fontSize: 9, fontWeight: "900" },
  statusTextActive: { color: "#FFFFFF" },
  loadHint: { backgroundColor: "#101419", borderRadius: 13, padding: 14, marginTop: 12 },
  loadHintTitle: { color: "#FFFFFF", fontSize: 12, fontWeight: "700" },
  loadHintText: { color: "#727E8A", fontSize: 10, lineHeight: 16, marginTop: 5 },
  primaryButton: {
    minHeight: 50, backgroundColor: "#FFFFFF", borderRadius: 12,
    alignItems: "center", justifyContent: "center", marginTop: 14,
  },
  primaryText: { color: "#0B0D10", fontSize: 12, fontWeight: "800" },
  disabledButton: { opacity: 0.55 },
  backLink: { marginTop: 14 },
  backLinkText: { color: "#6FC5FF", fontSize: 12 },
  errorTitle: { color: "#FFFFFF", fontSize: 20, fontWeight: "700" },
  errorText: { color: "#7E8794", textAlign: "center", lineHeight: 18, marginTop: 8 },
  historyButton: {
    minHeight: 43,
    borderRadius: 11,
    backgroundColor: "#252E37",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  historyButtonText: { color: "#E0E6EB", fontSize: 10, fontWeight: "800" },
  summaryCard: { backgroundColor: "#171A20", borderRadius: 20, padding: 22, marginBottom: 22 },
  summaryLabel: { color: "#8B95A2", fontSize: 12 },
  percentage: { color: "#FFFFFF", fontSize: 42, fontWeight: "700", marginTop: 10 },
  summaryText: { color: "#7E8794", marginTop: 6 },
  classesHeld: { color: "#5F6A76", fontSize: 10, marginTop: 8 },
  sectionTitle: { color: "#FFFFFF", fontSize: 18, fontWeight: "700", marginBottom: 12 },
  emptyCard: { backgroundColor: "#171A20", borderRadius: 17, padding: 18, marginBottom: 12 },
  emptyTitle: { color: "#FFFFFF", fontSize: 14, fontWeight: "700" },
  emptyText: { color: "#7E8794", lineHeight: 18, fontSize: 12, marginTop: 5 },
  studentCard: {
    backgroundColor: "#171A20", borderRadius: 18, padding: 17, marginBottom: 10,
    flexDirection: "row", alignItems: "center",
  },
  warningBadge: {
    alignSelf: "flex-start", flexDirection: "row", alignItems: "center",
    backgroundColor: "#2A211A", borderRadius: 8, paddingHorizontal: 8,
    paddingVertical: 5, marginTop: 8,
  },
  warningDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: "#FFB86B", marginRight: 6 },
  warningText: { color: "#FFB86B", fontSize: 10, fontWeight: "600" },
  recoveryText: { color: "#6FC5FF", fontSize: 10, marginTop: 7, lineHeight: 15 },
  percentageBox: { alignItems: "flex-end", marginLeft: 12 },
  studentPercentage: { color: "#FFB86B", fontSize: 20, fontWeight: "700" },
  attendedText: { color: "#68727D", fontSize: 10, marginTop: 3 },
});
