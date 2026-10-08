import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useCallback, useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";

import {
  AttendanceStudentDetailResponse,
  getStudentAttendanceDetail,
} from "../../services/api";

export default function StudentAttendanceDetailScreen() {
  const router = useRouter();
  const { course_id, student_id } =
    useLocalSearchParams<{ course_id?: string; student_id?: string }>();
  const courseId = Array.isArray(course_id) ? course_id[0] : course_id;
  const studentId = Array.isArray(student_id) ? student_id[0] : student_id;

  const [detail, setDetail] =
    useState<AttendanceStudentDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!courseId || !studentId) {
      setError("Course or student id is missing.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");
      setDetail(await getStudentAttendanceDetail(courseId, studentId));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't load student attendance."
      );
    } finally {
      setLoading(false);
    }
  }, [courseId, studentId]);

  useEffect(() => {
    void Promise.resolve().then(() => load());
  }, [load]);

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6FC5FF" />
          <Text style={styles.stateText}>Loading student...</Text>
        </View>
      </View>
    );
  }

  if (!detail) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>Student unavailable</Text>
          <Text style={styles.errorText}>{error || "Student not found."}</Text>
          <Pressable style={styles.primaryButton} onPress={() => void load()}>
            <Text style={styles.primaryText}>Retry</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.container}>
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <Text style={styles.back}>‹</Text>
        </Pressable>

        <Text style={styles.eyebrow}>ATTENDANCE PROFILE</Text>
        <Text style={styles.title}>{detail.name}</Text>
        <Text style={styles.subtitle}>
          {detail.roll_no} · Section {detail.section || "—"} · {detail.course_code}
        </Text>

        <View style={styles.heroCard}>
          <Text style={styles.heroLabel}>CURRENT ATTENDANCE</Text>
          <Text style={styles.percentage}>
            {detail.percentage == null ? "--" : Math.round(detail.percentage) + "%"}
          </Text>
          <Text style={styles.heroMeta}>
            {detail.attended}/{detail.total} counted classes
          </Text>

          <View
            style={[
              styles.statusBadge,
              detail.flagged ? styles.badgeDanger : styles.badgeGood,
            ]}
          >
            <Text style={styles.statusBadgeText}>
              {detail.flagged
                ? "Below " + detail.threshold_pct + "%"
                : "Above " + detail.threshold_pct + "%"}
            </Text>
          </View>

          {detail.flagged ? (
            <Text style={styles.recoveryText}>
              Needs {detail.classes_needed_to_recover} consecutive{" "}
              {detail.classes_needed_to_recover === 1 ? "class" : "classes"} to recover.
            </Text>
          ) : (
            <Text style={styles.recoveryTextGood}>
              Attendance is currently above the required threshold.
            </Text>
          )}
        </View>

        <View style={styles.actionRow}>
          <Pressable
            style={styles.actionButton}
            onPress={() =>
              router.push({
                pathname: "/attendance",
                params: { course_id: detail.course_id },
              })
            }
          >
            <Text style={styles.actionButtonText}>Take Attendance</Text>
          </Pressable>

          <Pressable
            style={styles.actionButton}
            onPress={() =>
              router.push({
                pathname: "/attendance/history",
                params: { course_id: detail.course_id },
              })
            }
          >
            <Text style={styles.actionButtonText}>History</Text>
          </Pressable>
        </View>

        <Text style={styles.sectionTitle}>Student history</Text>

        {detail.history.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No classes recorded</Text>
            <Text style={styles.emptyText}>
              This student does not have any recorded attendance sessions yet.
            </Text>
          </View>
        ) : (
          detail.history.map((row) => (
            <View key={row.class_date} style={styles.historyRow}>
              <View style={styles.historyMain}>
                <Text style={styles.historyDate}>{row.class_date}</Text>
                <Text style={styles.historyHint}>Recorded class session</Text>
              </View>

              <View
                style={[
                  styles.statusChip,
                  row.status === "present"
                    ? styles.presentChip
                    : row.status === "absent"
                      ? styles.absentChip
                      : styles.excusedChip,
                ]}
              >
                <Text
                  style={[
                    styles.statusChipText,
                    row.status === "present"
                      ? styles.presentText
                      : row.status === "absent"
                        ? styles.absentText
                        : styles.excusedText,
                  ]}
                >
                  {row.status.toUpperCase()}
                </Text>
              </View>
            </View>
          ))
        )}

        <View style={{ height: 45 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#0B0D10" },
  container: { padding: 20, paddingTop: 55, paddingBottom: 40 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 25 },
  stateText: { color: "#7E8794", marginTop: 12 },
  backButton: { alignSelf: "flex-start", paddingRight: 15 },
  back: { color: "#FFFFFF", fontSize: 38, lineHeight: 38 },
  eyebrow: { color: "#6FC5FF", fontSize: 9, fontWeight: "800", letterSpacing: 1.1 },
  title: { color: "#FFFFFF", fontSize: 26, fontWeight: "800", marginTop: 5 },
  subtitle: { color: "#7E8794", fontSize: 12, marginTop: 5, marginBottom: 20 },
  heroCard: { backgroundColor: "#171A20", borderRadius: 20, padding: 21, marginBottom: 13 },
  heroLabel: { color: "#8B95A2", fontSize: 10, fontWeight: "700" },
  percentage: { color: "#FFFFFF", fontSize: 45, fontWeight: "800", marginTop: 8 },
  heroMeta: { color: "#7B8792", fontSize: 11, marginTop: 4 },
  statusBadge: { alignSelf: "flex-start", borderRadius: 8, paddingHorizontal: 9, paddingVertical: 5, marginTop: 12 },
  badgeDanger: { backgroundColor: "#2A211A" },
  badgeGood: { backgroundColor: "#1B3025" },
  statusBadgeText: { color: "#FFFFFF", fontSize: 9, fontWeight: "800" },
  recoveryText: { color: "#FFB86B", fontSize: 10, lineHeight: 16, marginTop: 9 },
  recoveryTextGood: { color: "#72D6A0", fontSize: 10, lineHeight: 16, marginTop: 9 },
  actionRow: { flexDirection: "row", gap: 8, marginBottom: 24 },
  actionButton: {
    flex: 1, minHeight: 43, borderRadius: 11, backgroundColor: "#252E37",
    alignItems: "center", justifyContent: "center",
  },
  actionButtonText: { color: "#E0E6EB", fontSize: 10, fontWeight: "800" },
  sectionTitle: { color: "#FFFFFF", fontSize: 18, fontWeight: "700", marginBottom: 12 },
  emptyCard: { backgroundColor: "#171A20", borderRadius: 18, padding: 19 },
  emptyTitle: { color: "#FFFFFF", fontSize: 14, fontWeight: "700" },
  emptyText: { color: "#7E8995", fontSize: 11, lineHeight: 17, marginTop: 6 },
  historyRow: {
    backgroundColor: "#171A20", borderRadius: 16, padding: 15,
    marginBottom: 8, flexDirection: "row", alignItems: "center",
  },
  historyMain: { flex: 1, paddingRight: 8 },
  historyDate: { color: "#FFFFFF", fontSize: 12, fontWeight: "800" },
  historyHint: { color: "#66727E", fontSize: 9, marginTop: 4 },
  statusChip: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 6 },
  presentChip: { backgroundColor: "#1B3025" },
  absentChip: { backgroundColor: "#2A1B1E" },
  excusedChip: { backgroundColor: "#2A211A" },
  statusChipText: { fontSize: 8, fontWeight: "900" },
  presentText: { color: "#72D6A0" },
  absentText: { color: "#FF9B9B" },
  excusedText: { color: "#FFB86B" },
  primaryButton: {
    minHeight: 48, backgroundColor: "#FFFFFF", borderRadius: 12,
    alignItems: "center", justifyContent: "center", marginTop: 16,
  },
  primaryText: { color: "#0B0D10", fontSize: 12, fontWeight: "800" },
});
