import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  useLocalSearchParams,
  useRouter,
} from "expo-router";

import {
  getAcademicContext,
  getCourseAttendance,
  getMe,
  AttendanceCourseResponse,
  AttendanceStudent,
} from "../services/api";

export default function AttendanceScreen() {
  const router = useRouter();

  const { course_id } =
    useLocalSearchParams<{
      course_id?: string;
    }>();

  const [attendance, setAttendance] =
    useState<AttendanceCourseResponse | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadAttendance = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      let selectedCourseId =
        Array.isArray(course_id)
          ? course_id[0]
          : course_id;

      if (!selectedCourseId) {
        const me = await getMe();

        const context =
          await getAcademicContext(
            me.lecturer_id
          );

        selectedCourseId =
          context.selected_course?.id ||
          context.courses[0]?.id;
      }

      if (!selectedCourseId) {
        throw new Error(
          "No course is available for attendance."
        );
      }

      const data =
        await getCourseAttendance(
          selectedCourseId
        );

      setAttendance(data);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Couldn&apos;t load attendance."
      );
    } finally {
      setLoading(false);
    }
  }, [course_id]);

  useEffect(() => {
    void loadAttendance();
  }, [loadAttendance]);

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator
            size="large"
            color="#6FC5FF"
          />

          <Text style={styles.stateText}>
            Loading attendance...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !attendance) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>
            Attendance unavailable
          </Text>

          <Text style={styles.errorText}>
            {error ||
              "No attendance data found."}
          </Text>

          <Pressable
            style={styles.retryButton}
            onPress={loadAttendance}
          >
            <Text style={styles.retryText}>
              Retry
            </Text>
          </Pressable>

          <Pressable
            style={styles.backLink}
            onPress={() => router.back()}
          >
            <Text
              style={
                styles.backLinkText
              }
            >
              Go back
            </Text>
          </Pressable>
        </View>
      </View>
    );
  }

  const flaggedStudents =
    attendance.students.filter(
      (student) => student.flagged
    );

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={
          styles.container
        }
        showsVerticalScrollIndicator={false}
      >
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>
            ‹
          </Text>
        </Pressable>

        <Text style={styles.title}>
          Attendance
        </Text>

        <Text style={styles.subtitle}>
          {attendance.course_code} ·{" "}
          {attendance.section}
        </Text>

        {/* SUMMARY */}

        <View style={styles.summary}>
          <Text style={styles.summaryLabel}>
            Class Average
          </Text>

          <Text style={styles.percentage}>
            {attendance.class_average_pct ==
            null
              ? "--"
              : `${Math.round(
                  attendance.class_average_pct
                )}%`}
          </Text>

          <Text style={styles.summaryText}>
            {attendance.present_last_class}{" "}
            present ·{" "}
            {attendance.absent_last_class}{" "}
            absent
          </Text>

          <Text style={styles.classesHeld}>
            {attendance.classes_held} classes held
          </Text>
        </View>

        {/* FLAGGED */}

        <Text style={styles.sectionTitle}>
          Students Below{" "}
          {attendance.threshold_pct}%
        </Text>

        {flaggedStudents.length ===
        0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>
              All students are on track
            </Text>

            <Text style={styles.emptyText}>
              No students are currently below
              the attendance threshold.
            </Text>
          </View>
        ) : (
          flaggedStudents.map(
            (student) => (
              <StudentCard
                key={student.student_id}
                student={student}
              />
            )
          )
        )}

        <Text style={styles.note}>
          {attendance.flagged_count} students
          currently flagged.
        </Text>

        <View
          style={{ height: 80 }}
        />
      </ScrollView>
    </View>
  );
}

function StudentCard({
  student,
}: {
  student: AttendanceStudent;
}) {
  const percentage =
    student.percentage == null
      ? null
      : Math.round(
          student.percentage
        );

  return (
    <View style={styles.studentCard}>
      <View style={styles.studentInfo}>
        <Text style={styles.rollNo}>
          {student.roll_no}
        </Text>

        <Text style={styles.studentName}>
          {student.name}
        </Text>

        <View
          style={
            styles.warningBadge
          }
        >
          <View
            style={styles.warningDot}
          />

          <Text style={styles.warningText}>
            Below 75%
          </Text>
        </View>

        <Text style={styles.recoveryText}>
          Needs{" "}
          {student.classes_needed_to_recover}{" "}
          consecutive class
          {student.classes_needed_to_recover ===
          1
            ? ""
            : "es"}{" "}
          to recover
        </Text>
      </View>

      <View
        style={styles.percentageBox}
      >
        <Text
          style={styles.studentPercentage}
        >
          {percentage == null
            ? "--"
            : `${percentage}%`}
        </Text>

        <Text
          style={styles.attendedText}
        >
          {student.attended}/
          {student.total}
        </Text>
      </View>
    </View>
  );
}

const styles =
  StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: "#0B0D10",
    },

    container: {
      padding: 20,
      paddingTop: 55,
    },

    center: {
      flex: 1,
      alignItems: "center",
      justifyContent: "center",
      padding: 25,
    },

    stateText: {
      color: "#7E8794",
      marginTop: 12,
    },

    errorTitle: {
      color: "#FFFFFF",
      fontSize: 20,
      fontWeight: "700",
    },

    errorText: {
      color: "#7E8794",
      textAlign: "center",
      lineHeight: 19,
      marginTop: 8,
    },

    retryButton: {
      backgroundColor: "#FFFFFF",
      borderRadius: 10,
      paddingHorizontal: 18,
      paddingVertical: 10,
      marginTop: 20,
    },

    retryText: {
      color: "#0B0D10",
      fontWeight: "700",
    },

    backLink: {
      marginTop: 14,
    },

    backLinkText: {
      color: "#6FC5FF",
      fontSize: 12,
    },

    backButton: {
      alignSelf: "flex-start",
      paddingRight: 15,
    },

    back: {
      color: "#FFFFFF",
      fontSize: 38,
      lineHeight: 38,
    },

    title: {
      color: "#FFFFFF",
      fontSize: 28,
      fontWeight: "700",
      marginTop: 8,
    },

    subtitle: {
      color: "#7E8794",
      fontSize: 13,
      marginTop: 5,
      marginBottom: 25,
    },

    summary: {
      backgroundColor: "#171A20",
      borderRadius: 20,
      padding: 22,
      marginBottom: 28,
    },

    summaryLabel: {
      color: "#8B95A2",
      fontSize: 12,
    },

    percentage: {
      color: "#FFFFFF",
      fontSize: 42,
      fontWeight: "700",
      marginTop: 10,
    },

    summaryText: {
      color: "#7E8794",
      marginTop: 6,
    },

    classesHeld: {
      color: "#5F6A76",
      fontSize: 10,
      marginTop: 8,
    },

    sectionTitle: {
      color: "#FFFFFF",
      fontSize: 18,
      fontWeight: "700",
      marginBottom: 12,
    },

    emptyCard: {
      backgroundColor: "#171A20",
      borderRadius: 17,
      padding: 18,
    },

    emptyTitle: {
      color: "#FFFFFF",
      fontSize: 14,
      fontWeight: "700",
    },

    emptyText: {
      color: "#7E8794",
      lineHeight: 18,
      fontSize: 12,
      marginTop: 5,
    },

    studentCard: {
      backgroundColor: "#171A20",
      borderRadius: 18,
      padding: 17,
      marginBottom: 10,
      flexDirection: "row",
      alignItems: "center",
    },

    studentInfo: {
      flex: 1,
    },

    rollNo: {
      color: "#FFFFFF",
      fontSize: 15,
      fontWeight: "700",
    },

    studentName: {
      color: "#A7B0BA",
      fontSize: 12,
      marginTop: 3,
    },

    warningBadge: {
      alignSelf: "flex-start",
      flexDirection: "row",
      alignItems: "center",
      backgroundColor: "#2A211A",
      borderRadius: 8,
      paddingHorizontal: 8,
      paddingVertical: 5,
      marginTop: 8,
    },

    warningDot: {
      width: 6,
      height: 6,
      borderRadius: 3,
      backgroundColor: "#FFB86B",
      marginRight: 6,
    },

    warningText: {
      color: "#FFB86B",
      fontSize: 10,
      fontWeight: "600",
    },

    recoveryText: {
      color: "#6FC5FF",
      fontSize: 10,
      marginTop: 7,
      lineHeight: 15,
    },

    percentageBox: {
      alignItems: "flex-end",
      marginLeft: 12,
    },

    studentPercentage: {
      color: "#FFB86B",
      fontSize: 20,
      fontWeight: "700",
    },

    attendedText: {
      color: "#68727D",
      fontSize: 10,
      marginTop: 3,
    },

    note: {
      color: "#626C78",
      fontSize: 10,
      lineHeight: 17,
      marginTop: 15,
    },
  });