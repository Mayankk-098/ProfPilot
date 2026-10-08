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
  AttendanceCourseResponse,
  AttendanceSessionSummary,
  getCourseAttendance,
  getAttendanceHistory,
} from "../../services/api";

export default function AttendanceHistoryScreen() {
  const router = useRouter();
  const { course_id } = useLocalSearchParams<{ course_id?: string }>();
  const courseId = Array.isArray(course_id) ? course_id[0] : course_id;

  const [attendance, setAttendance] = useState<AttendanceCourseResponse | null>(null);
  const [history, setHistory] = useState<AttendanceSessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!courseId) {
      setError("Course id is missing.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");
      const [attendanceData, historyData] = await Promise.all([
        getCourseAttendance(courseId),
        getAttendanceHistory(courseId),
      ]);
      setAttendance(attendanceData);
      setHistory(historyData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't load attendance history."
      );
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    void Promise.resolve().then(() => load());
  }, [load]);

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6FC5FF" />
          <Text style={styles.stateText}>Loading history...</Text>
        </View>
      </View>
    );
  }

  if (!attendance) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>History unavailable</Text>
          <Text style={styles.errorText}>{error || "Course not found."}</Text>
          <Pressable style={styles.primaryButton} onPress={() => void load()}>
            <Text style={styles.primaryText}>Retry</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        <Pressable onPress={() => router.back()} style={styles.backButton}>
          <Text style={styles.back}>‹</Text>
        </Pressable>

        <Text style={styles.eyebrow}>COURSE WORKSPACE</Text>
        <Text style={styles.title}>Attendance History</Text>
        <Text style={styles.subtitle}>
          {attendance.course_code} · {attendance.section}
        </Text>

        {error ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        <View style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>Recorded classes</Text>
          <Text style={styles.totalClasses}>{history.length}</Text>
          <Text style={styles.summaryText}>
            {attendance.total_students} students in the current roster
          </Text>
        </View>

        <Text style={styles.sectionTitle}>Class sessions</Text>

        {history.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No attendance recorded yet</Text>
            <Text style={styles.emptyText}>
              Once you save a class session, it will appear here with its
              present, absent and excused counts.
            </Text>
          </View>
        ) : (
          history.map((session) => (
            <SessionCard
              key={session.class_date}
              session={session}
              onOpen={() =>
                router.push({
                  pathname: "/attendance",
                  params: {
                    course_id: attendance.course_id,
                    class_date: session.class_date,
                  },
                })
              }
            />
          ))
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

function SessionCard({
  session,
  onOpen,
}: {
  session: AttendanceSessionSummary;
  onOpen: () => void;
}) {
  return (
    <View style={styles.sessionCard}>
      <View style={styles.sessionMain}>
        <Text style={styles.sessionDate}>{session.class_date}</Text>

        <View style={styles.statRow}>
          <Text style={styles.presentStat}>{session.present} present</Text>
          <Text style={styles.absentStat}>{session.absent} absent</Text>
          {session.excused > 0 ? (
            <Text style={styles.excusedStat}>{session.excused} excused</Text>
          ) : null}
        </View>

        <Text style={styles.recordCount}>
          {session.total_records} attendance records
        </Text>
      </View>

      <Pressable style={styles.openButton} onPress={onOpen}>
        <Text style={styles.openButtonText}>Open</Text>
      </Pressable>
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
  title: { color: "#FFFFFF", fontSize: 27, fontWeight: "800", marginTop: 5 },
  subtitle: { color: "#7E8794", fontSize: 13, marginTop: 5, marginBottom: 20 },
  errorBanner: {
    backgroundColor: "#2A1B1E", borderWidth: 1, borderColor: "#513036",
    borderRadius: 12, padding: 12, marginBottom: 14,
  },
  errorText: { color: "#FFB0B0", fontSize: 11, lineHeight: 17 },
  summaryCard: {
    backgroundColor: "#171A20", borderRadius: 20, padding: 21, marginBottom: 25,
  },
  summaryLabel: { color: "#8B95A2", fontSize: 11 },
  totalClasses: { color: "#FFFFFF", fontSize: 39, fontWeight: "800", marginTop: 8 },
  summaryText: { color: "#737F8A", fontSize: 11, marginTop: 5 },
  sectionTitle: { color: "#FFFFFF", fontSize: 18, fontWeight: "700", marginBottom: 12 },
  emptyCard: { backgroundColor: "#171A20", borderRadius: 18, padding: 20, marginBottom: 10 },
  emptyTitle: { color: "#FFFFFF", fontSize: 14, fontWeight: "700" },
  emptyText: { color: "#7E8995", fontSize: 11, lineHeight: 17, marginTop: 7 },
  sessionCard: {
    backgroundColor: "#171A20", borderRadius: 17, padding: 16, marginBottom: 9,
    flexDirection: "row", alignItems: "center",
  },
  sessionMain: { flex: 1, paddingRight: 10 },
  sessionDate: { color: "#FFFFFF", fontSize: 15, fontWeight: "800" },
  statRow: { flexDirection: "row", flexWrap: "wrap", gap: 9, marginTop: 8 },
  presentStat: { color: "#72D6A0", fontSize: 10, fontWeight: "700" },
  absentStat: { color: "#FF9B9B", fontSize: 10, fontWeight: "700" },
  excusedStat: { color: "#FFB86B", fontSize: 10, fontWeight: "700" },
  recordCount: { color: "#66727E", fontSize: 9, marginTop: 7 },
  openButton: {
    backgroundColor: "#252E37", borderRadius: 10,
    paddingHorizontal: 13, paddingVertical: 9,
  },
  openButtonText: { color: "#E1E7EC", fontSize: 10, fontWeight: "800" },
  primaryButton: {
    minHeight: 48, backgroundColor: "#FFFFFF", borderRadius: 12,
    alignItems: "center", justifyContent: "center", marginTop: 16,
  },
  primaryText: { color: "#0B0D10", fontSize: 12, fontWeight: "800" },
});
