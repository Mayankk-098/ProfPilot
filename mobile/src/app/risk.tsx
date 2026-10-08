import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "expo-router";

import {
  CourseRisk,
  getRiskRadar,
  RecoveryPlan,
  RiskRadarResponse,
} from "../services/api";

function levelLabel(level: CourseRisk["risk_level"]) {
  if (level === "high") return "HIGH RISK";
  if (level === "medium") return "WATCH";
  if (level === "low") return "LOW SIGNAL";
  return "ON TRACK";
}

function levelTone(level: CourseRisk["risk_level"]) {
  if (level === "high") return styles.high;
  if (level === "medium") return styles.medium;
  if (level === "low") return styles.low;
  return styles.onTrack;
}

function RecoveryCard({ recovery }: { recovery: RecoveryPlan }) {
  const hasRecovery = recovery.classes_needed_to_recover > 0;

  return (
    <View style={styles.recoveryCard}>
      <View style={styles.recoveryHeader}>
        <View style={styles.recoveryIdentity}>
          <Text style={styles.recoveryRoll}>{recovery.roll_no}</Text>
          <Text style={styles.recoveryName}>{recovery.name}</Text>
        </View>
        <Text style={styles.recoveryPct}>
          {recovery.current_attendance == null
            ? "--"
            : Math.round(recovery.current_attendance) + "%"}
        </Text>
      </View>

      {hasRecovery ? (
        <View style={styles.planBox}>
          <Text style={styles.planNumber}>
            {recovery.classes_needed_to_recover}
          </Text>
          <View style={styles.planCopy}>
            <Text style={styles.planTitle}>CONSECUTIVE CLASSES</Text>
            <Text style={styles.planText}>{recovery.action}</Text>
          </View>
        </View>
      ) : (
        <Text style={styles.planText}>{recovery.action}</Text>
      )}

      {recovery.projected_attendance_after_recovery != null ? (
        <Text style={styles.projected}>
          Projected after recovery:{" "}
          {Math.round(recovery.projected_attendance_after_recovery)}%
        </Text>
      ) : null}
    </View>
  );
}

function CourseRiskCard({ course }: { course: CourseRisk }) {
  const router = useRouter();

  return (
    <View style={styles.courseCard}>
      <View style={styles.courseHeader}>
        <View style={styles.courseIdentity}>
          <Text style={styles.courseCode}>{course.course_code}</Text>
          <Text style={styles.courseName}>
            {course.short_name || course.course_name}
          </Text>
          <Text style={styles.courseSection}>Section {course.section}</Text>
        </View>

        <View style={[styles.levelBadge, levelTone(course.risk_level)]}>
          <Text style={styles.levelText}>{levelLabel(course.risk_level)}</Text>
          <Text style={styles.scoreText}>{Math.round(course.risk_score)}</Text>
        </View>
      </View>

      <Text style={styles.headline}>{course.headline}</Text>

      <View style={styles.metricsRow}>
        <Metric
          label="Progress"
          value={Math.round(course.academic_progress.actual) + "%"}
          detail={
            course.academic_progress.gap > 0
              ? Math.round(course.academic_progress.gap) + "% behind"
              : "On plan"
          }
        />
        <Metric
          label="Attendance"
          value={
            course.attendance.class_average_pct == null
              ? "--"
              : Math.round(course.attendance.class_average_pct) + "%"
          }
          detail={course.attendance.flagged_count + " flagged"}
        />
        <Metric
          label="Forecast"
          value={
            course.forecast.predicted_completion
              ? course.forecast.predicted_completion.slice(5)
              : "--"
          }
          detail={
            course.forecast.confidence || "More data needed"
          }
        />
      </View>

      {course.drivers.length > 0 ? (
        <View style={styles.drivers}>
          <Text style={styles.subsectionLabel}>WHY THIS FLAG EXISTS</Text>
          {course.drivers.slice(0, 3).map((driver) => (
            <View
              key={course.course_id + "-" + driver.type}
              style={styles.driverRow}
            >
              <View style={styles.driverDot} />
              <Text style={styles.driverText}>{driver.message}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {course.recovery_plan.length > 0 ? (
        <View style={styles.recoverySection}>
          <Text style={styles.subsectionLabel}>RECOVERY PLANNER</Text>
          <Text style={styles.sectionCopy}>
            Students who need attendance recovery
          </Text>

          {course.recovery_plan.slice(0, 5).map((recovery) => (
            <Pressable
              key={recovery.student_id}
              onPress={() =>
                router.push({
                  pathname: "/attendance/student" as any,
                  params: {
                    course_id: course.course_id,
                    student_id: recovery.student_id,
                  },
                })
              }
            >
              <RecoveryCard recovery={recovery} />
            </Pressable>
          ))}
        </View>
      ) : course.risk_level === "on_track" ? (
        <Text style={styles.goodText}>
          No student recovery actions are currently required.
        </Text>
      ) : null}
    </View>
  );
}

function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricDetail}>{detail}</Text>
    </View>
  );
}

export default function RiskRadarScreen() {
  const router = useRouter();
  const [data, setData] = useState<RiskRadarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      setData(await getRiskRadar());
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load academic risk radar."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6FC5FF" />
          <Text style={styles.stateText}>Building academic risk radar...</Text>
        </View>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>Risk radar unavailable</Text>
          <Text style={styles.errorText}>
            {error || "No academic data found."}
          </Text>
          <Pressable style={styles.primaryButton} onPress={() => void load()}>
            <Text style={styles.primaryText}>Retry</Text>
          </Pressable>
          <Pressable style={styles.backLink} onPress={() => router.back()}>
            <Text style={styles.backLinkText}>Go back</Text>
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
        <View style={styles.topBar}>
          <Pressable onPress={() => router.back()} style={styles.backButton}>
            <Text style={styles.back}>‹</Text>
          </Pressable>
          <View style={styles.topBarText}>
            <Text style={styles.eyebrow}>ACADEMIC INTELLIGENCE</Text>
            <Text style={styles.title}>Risk Radar</Text>
            <Text style={styles.subtitle}>
              What needs attention before it becomes a bigger problem.
            </Text>
          </View>
          <Pressable onPress={() => void load()} style={styles.refreshButton}>
            <Text style={styles.refreshText}>↻</Text>
          </Pressable>
        </View>

        <View style={styles.summaryCard}>
          <SummaryStat
            number={data.summary.high_risk_courses}
            label="High risk"
          />
          <View style={styles.summaryDivider} />
          <SummaryStat
            number={data.summary.medium_risk_courses}
            label="Watch"
          />
          <View style={styles.summaryDivider} />
          <SummaryStat
            number={data.summary.flagged_students}
            label="Students flagged"
          />
        </View>

        <Text style={styles.generated}>
          Analysis generated for {data.generated_for}
        </Text>

        {data.courses.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No courses yet</Text>
            <Text style={styles.emptyText}>
              Create a course, add a syllabus, and build attendance history
              to activate the radar.
            </Text>
          </View>
        ) : (
          data.courses.map((course) => (
            <CourseRiskCard key={course.course_id} course={course} />
          ))
        )}

        <View style={{ height: 70 }} />
      </ScrollView>
    </View>
  );
}

function SummaryStat({ number, label }: { number: number; label: string }) {
  return (
    <View style={styles.summaryStat}>
      <Text style={styles.summaryNumber}>{number}</Text>
      <Text style={styles.summaryLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#0B0D10" },
  container: { padding: 20, paddingTop: 55, paddingBottom: 35 },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 25,
  },
  stateText: { color: "#7E8794", marginTop: 12 },
  errorTitle: { color: "#FFFFFF", fontSize: 20, fontWeight: "700" },
  errorText: {
    color: "#7E8794",
    textAlign: "center",
    lineHeight: 18,
    marginTop: 10,
  },
  primaryButton: {
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 22,
    paddingVertical: 12,
    borderRadius: 11,
    marginTop: 20,
  },
  primaryText: { color: "#0B0D10", fontWeight: "800" },
  backLink: { marginTop: 15, padding: 8 },
  backLinkText: { color: "#7E8794", fontSize: 12 },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
  },
  backButton: { marginRight: 10, paddingRight: 7 },
  back: { color: "#FFFFFF", fontSize: 38, lineHeight: 38 },
  topBarText: { flex: 1 },
  eyebrow: {
    color: "#6FC5FF",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 1.1,
  },
  title: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "800",
    marginTop: 3,
  },
  subtitle: {
    color: "#76818D",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },
  refreshButton: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: "#171A20",
    alignItems: "center",
    justifyContent: "center",
  },
  refreshText: { color: "#DDE4EA", fontSize: 21 },
  summaryCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 17,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 9,
  },
  summaryStat: { flex: 1, alignItems: "center" },
  summaryNumber: { color: "#FFFFFF", fontSize: 22, fontWeight: "800" },
  summaryLabel: {
    color: "#74808C",
    fontSize: 9,
    fontWeight: "700",
    marginTop: 4,
    textAlign: "center",
  },
  summaryDivider: {
    width: 1,
    height: 33,
    backgroundColor: "#2A3037",
  },
  generated: {
    color: "#5F6A76",
    fontSize: 9,
    marginBottom: 17,
  },
  courseCard: {
    backgroundColor: "#171A20",
    borderRadius: 20,
    padding: 17,
    marginBottom: 13,
  },
  courseHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  courseIdentity: { flex: 1, paddingRight: 10 },
  courseCode: {
    color: "#6FC5FF",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.7,
  },
  courseName: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "700",
    marginTop: 4,
  },
  courseSection: {
    color: "#6E7985",
    fontSize: 10,
    marginTop: 4,
  },
  levelBadge: {
    minWidth: 65,
    borderRadius: 11,
    paddingHorizontal: 8,
    paddingVertical: 7,
    alignItems: "center",
  },
  high: { backgroundColor: "#392225" },
  medium: { backgroundColor: "#383122" },
  low: { backgroundColor: "#252C31" },
  onTrack: { backgroundColor: "#1D3026" },
  levelText: { color: "#E7EDF2", fontSize: 8, fontWeight: "800" },
  scoreText: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "800",
    marginTop: 2,
  },
  headline: {
    color: "#B9C1C9",
    fontSize: 11,
    lineHeight: 17,
    marginTop: 13,
  },
  metricsRow: {
    flexDirection: "row",
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: "#252A31",
    borderBottomWidth: 1,
    borderBottomColor: "#252A31",
    paddingVertical: 12,
  },
  metric: { flex: 1, paddingHorizontal: 5 },
  metricLabel: {
    color: "#68737F",
    fontSize: 8,
    fontWeight: "700",
    letterSpacing: 0.7,
  },
  metricValue: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "800",
    marginTop: 4,
  },
  metricDetail: {
    color: "#7E8995",
    fontSize: 8,
    marginTop: 3,
  },
  drivers: { marginTop: 15 },
  subsectionLabel: {
    color: "#6FC5FF",
    fontSize: 8,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  driverRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginTop: 9,
  },
  driverDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: "#7B8793",
    marginTop: 5,
    marginRight: 8,
  },
  driverText: {
    flex: 1,
    color: "#AEB7C0",
    fontSize: 10,
    lineHeight: 15,
  },
  recoverySection: { marginTop: 18 },
  sectionCopy: {
    color: "#7F8A96",
    fontSize: 10,
    marginTop: 4,
  },
  recoveryCard: {
    backgroundColor: "#101318",
    borderRadius: 13,
    padding: 12,
    marginTop: 8,
  },
  recoveryHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  recoveryIdentity: { flex: 1 },
  recoveryRoll: {
    color: "#66727E",
    fontSize: 8,
    fontWeight: "700",
  },
  recoveryName: {
    color: "#E8EDF2",
    fontSize: 12,
    fontWeight: "700",
    marginTop: 3,
  },
  recoveryPct: {
    color: "#FFB0B0",
    fontSize: 17,
    fontWeight: "800",
  },
  planBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#171C22",
    borderRadius: 10,
    padding: 9,
    marginTop: 9,
  },
  planNumber: {
    color: "#FFFFFF",
    fontSize: 20,
    fontWeight: "800",
    width: 34,
  },
  planCopy: { flex: 1 },
  planTitle: {
    color: "#6FC5FF",
    fontSize: 9,
    fontWeight: "800",
  },
  planText: {
    color: "#B1BAC3",
    fontSize: 9,
    lineHeight: 14,
  },
  projected: {
    color: "#6F7B87",
    fontSize: 8,
    marginTop: 8,
  },
  goodText: {
    color: "#72D6A0",
    fontSize: 10,
    marginTop: 15,
  },
  emptyCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 22,
    alignItems: "center",
  },
  emptyTitle: { color: "#FFFFFF", fontSize: 15, fontWeight: "700" },
  emptyText: {
    color: "#7F8B97",
    fontSize: 11,
    lineHeight: 17,
    textAlign: "center",
    marginTop: 7,
  },
});
