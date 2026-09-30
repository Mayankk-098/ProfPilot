import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";

import {
  getCourse,
  CourseDetail,
} from "../../services/api";


export default function CourseDetailsScreen() {
  const router = useRouter();

  const { id } = useLocalSearchParams<{
    id: string;
  }>();

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {
    if (id) {
      loadCourse(id);
    }
  }, [id]);


  async function loadCourse(courseId: string) {
    try {
      setLoading(true);
      setError("");

      const data = await getCourse(courseId);

      setCourse(data);
    } catch (err) {
      console.error(err);

      setError(
        "Couldn't load this course. Make sure the ProfPilot server is running."
      );
    } finally {
      setLoading(false);
    }
  }


  // --------------------------------
  // LOADING
  // --------------------------------

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.stateContainer}>
          <ActivityIndicator
            size="large"
            color="#6FC5FF"
          />

          <Text style={styles.stateText}>
            Loading course...
          </Text>
        </View>
      </View>
    );
  }


  // --------------------------------
  // ERROR
  // --------------------------------

  if (error || !course) {
    return (
      <View style={styles.screen}>
        <View style={styles.stateContainer}>
          <Text style={styles.errorTitle}>
            Course unavailable
          </Text>

          <Text style={styles.errorText}>
            {error || "Course not found."}
          </Text>

          <Pressable
            style={styles.retryButton}
            onPress={() => {
              if (id) {
                loadCourse(id);
              }
            }}
          >
            <Text style={styles.retryText}>
              Retry
            </Text>
          </Pressable>

          <Pressable
            onPress={() => router.back()}
            style={styles.backLinkButton}
          >
            <Text style={styles.backLink}>
              Go back
            </Text>
          </Pressable>
        </View>
      </View>
    );
  }


  const isBehind =
    course.progress <
    course.planned_progress;


  return (
    <View style={styles.screen}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >

        {/* -------------------------------- */}
        {/* BACK */}
        {/* -------------------------------- */}

        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>‹</Text>
        </Pressable>


        {/* -------------------------------- */}
        {/* COURSE HEADER */}
        {/* -------------------------------- */}

        <View style={styles.header}>
          <Text style={styles.code}>
            {course.code} · {course.section}
          </Text>

          <Text style={styles.title}>
            {course.name}
          </Text>

          <Text style={styles.department}>
            {course.department}
          </Text>
        </View>


        {/* -------------------------------- */}
        {/* PROF PILOT ANALYSIS */}
        {/* -------------------------------- */}

        <View style={styles.aiCard}>
          <Text style={styles.aiLabel}>
            PROFPILOT ANALYSIS
          </Text>

          <Text style={styles.aiTitle}>
            {isBehind
              ? "Course is behind planned pace"
              : "Course is progressing well"}
          </Text>

          <Text style={styles.aiText}>
            Current syllabus completion is{" "}
            <Text style={styles.highlight}>
              {course.progress}%
            </Text>
            , compared with a planned{" "}
            <Text style={styles.highlight}>
              {course.planned_progress}%
            </Text>
            .
          </Text>


          <View style={styles.aiDivider} />


          <View style={styles.aiStats}>

            <View style={styles.aiStat}>
              <Text style={styles.statLabel}>
                Current pace
              </Text>

              <Text style={styles.statValue}>
                {course.current_pace.toFixed(2)}
              </Text>

              <Text style={styles.statUnit}>
                topics / class
              </Text>
            </View>


            <View style={styles.aiStat}>
              <Text style={styles.statLabel}>
                Required pace
              </Text>

              <Text style={styles.statValue}>
                {course.required_pace.toFixed(2)}
              </Text>

              <Text style={styles.statUnit}>
                topics / class
              </Text>
            </View>

          </View>


          <View style={styles.aiDivider} />


          <View style={styles.completionRow}>

            <View style={styles.completionBox}>
              <Text style={styles.statLabel}>
                Predicted completion
              </Text>

              <Text style={styles.completionDate}>
                {course.predicted_completion}
              </Text>
            </View>


            <View style={styles.completionBox}>
              <Text style={styles.statLabel}>
                Planned completion
              </Text>

              <Text style={styles.completionDate}>
                {course.planned_completion}
              </Text>
            </View>

          </View>
        </View>


        {/* -------------------------------- */}
        {/* COURSE WORKSPACE */}
        {/* -------------------------------- */}

        <Text style={styles.sectionTitle}>
          Course Workspace
        </Text>


        <View style={styles.quickGrid}>

          <ActionCard
            icon="◎"
            title="Syllabus"
            subtitle="View course topics"
          />

          <ActionCard
            icon="◷"
            title="Lecture Plan"
            subtitle="Plan upcoming classes"
          />

          <ActionCard
            icon="✓"
            title="Attendance"
            subtitle={`${course.total_students} students`}
          />

          <ActionCard
            icon="✦"
            title="AI Insights"
            subtitle="Ask about this course"
          />

        </View>


        {/* -------------------------------- */}
        {/* SYLLABUS */}
        {/* -------------------------------- */}

        <View style={styles.sectionHeader}>

          <Text style={styles.sectionTitle}>
            Syllabus
          </Text>

          <Text style={styles.viewAll}>
            {course.progress}% complete
          </Text>

        </View>


        {course.syllabus.map((unit) => (

          <View
            style={styles.unitCard}
            key={unit.id}
          >

            <View style={styles.unitHeader}>

              <Text style={styles.unitName}>
                {unit.name}
              </Text>

              <Text style={styles.unitProgress}>
                {unit.progress}%
              </Text>

            </View>


            <View style={styles.unitProgressTrack}>

              <View
                style={[
                  styles.unitProgressFill,
                  {
                    width: `${unit.progress}%`,
                  },
                ]}
              />

            </View>


            {unit.topics.map((topic) => (

              <View
                key={topic.id}
                style={styles.topicRow}
              >

                <View
                  style={[
                    styles.topicDot,
                    topic.completed
                      ? styles.completedDot
                      : styles.pendingDot,
                  ]}
                />

                <Text
                  style={[
                    styles.topicText,
                    topic.completed &&
                      styles.completedTopic,
                  ]}
                >
                  {topic.name}
                </Text>


                {topic.completed && (
                  <Text style={styles.check}>
                    ✓
                  </Text>
                )}

              </View>

            ))}

          </View>

        ))}


        {/* -------------------------------- */}
        {/* ATTENDANCE SUMMARY */}
        {/* -------------------------------- */}

        <Text style={styles.sectionTitle}>
          Attendance
        </Text>


        <View style={styles.attendanceCard}>

          <View>
            <Text style={styles.attendanceLabel}>
              Today's attendance
            </Text>

            <Text style={styles.attendanceValue}>
              {course.present_today}
              <Text style={styles.attendanceSecondary}>
                {" "} / {course.total_students}
              </Text>
            </Text>

          </View>


          <View style={styles.attendanceRight}>

            <Text style={styles.attendancePercent}>
              {Math.round(
                (course.present_today /
                  course.total_students) *
                  100
              )}
              %
            </Text>

            <Text style={styles.attendanceSubtext}>
              present
            </Text>

          </View>

        </View>


        {/* -------------------------------- */}
        {/* RECENT LECTURES */}
        {/* -------------------------------- */}

        <Text style={styles.sectionTitle}>
          Recent Lectures
        </Text>


        {course.lectures
          .slice()
          .reverse()
          .slice(0, 5)
          .map((lecture) => (

            <View
              style={styles.lectureCard}
              key={lecture.id}
            >

              <View style={styles.lectureDate}>
                <Text style={styles.lectureDateText}>
                  {lecture.date.split(" ")[0]}
                </Text>
              </View>


              <View style={styles.lectureInfo}>

                <Text style={styles.lectureDateFull}>
                  {lecture.date}
                </Text>

                <Text style={styles.lectureDescription}>
                  {lecture.description}
                </Text>

                <Text style={styles.lectureDuration}>
                  {lecture.duration} minutes
                </Text>

              </View>

            </View>

          ))}


        {/* -------------------------------- */}
        {/* AI QUESTION */}
        {/* -------------------------------- */}

        <Pressable
          style={styles.askCard}
          onPress={() => {
            router.push("/ai");
          }}
        >

          <View style={styles.askIcon}>
            <Text style={styles.askIconText}>
              ✦
            </Text>
          </View>


          <View style={styles.askContent}>

            <Text style={styles.askTitle}>
              Ask ProfPilot about this course
            </Text>

            <Text style={styles.askSubtitle}>
              Ask about syllabus progress, lectures,
              attendance or what-if scenarios.
            </Text>

          </View>


          <Text style={styles.askArrow}>
            ›
          </Text>

        </Pressable>


        <View style={{ height: 30 }} />

      </ScrollView>
    </View>
  );
}


// ========================================
// ACTION CARD
// ========================================

function ActionCard({
  icon,
  title,
  subtitle,
}: {
  icon: string;
  title: string;
  subtitle: string;
}) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.actionCard,
        pressed && styles.pressed,
      ]}
    >

      <Text style={styles.actionIcon}>
        {icon}
      </Text>

      <Text style={styles.actionTitle}>
        {title}
      </Text>

      <Text style={styles.actionSubtitle}>
        {subtitle}
      </Text>

    </Pressable>
  );
}


// ========================================
// STYLES
// ========================================

const styles = StyleSheet.create({

  screen: {
    flex: 1,
    backgroundColor: "#0B0D10",
  },

  scroll: {
    flex: 1,
  },

  container: {
    paddingHorizontal: 20,
    paddingTop: 55,
    paddingBottom: 40,
  },

  stateContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 30,
  },

  stateText: {
    color: "#7E8794",
    fontSize: 13,
    marginTop: 15,
  },

  errorTitle: {
    color: "#FFFFFF",
    fontSize: 20,
    fontWeight: "700",
    marginBottom: 8,
  },

  errorText: {
    color: "#7E8794",
    fontSize: 13,
    textAlign: "center",
    lineHeight: 20,
    marginBottom: 20,
  },

  retryButton: {
    backgroundColor: "#FFFFFF",
    borderRadius: 11,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },

  retryText: {
    color: "#0B0D10",
    fontSize: 12,
    fontWeight: "700",
  },

  backLinkButton: {
    marginTop: 15,
  },

  backLink: {
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

  header: {
    marginTop: 8,
    marginBottom: 23,
  },

  code: {
    color: "#6FC5FF",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.5,
  },

  title: {
    color: "#FFFFFF",
    fontSize: 27,
    lineHeight: 33,
    fontWeight: "700",
    marginTop: 8,
  },

  department: {
    color: "#75808D",
    fontSize: 12,
    marginTop: 6,
  },

  aiCard: {
    backgroundColor: "#121820",
    borderRadius: 20,
    padding: 20,
    marginBottom: 28,
    borderWidth: 1,
    borderColor: "#1E2A35",
  },

  aiLabel: {
    color: "#6FC5FF",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.1,
  },

  aiTitle: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "700",
    marginTop: 9,
  },

  aiText: {
    color: "#929DA9",
    fontSize: 13,
    lineHeight: 20,
    marginTop: 8,
  },

  highlight: {
    color: "#6FC5FF",
    fontWeight: "700",
  },

  aiDivider: {
    height: 1,
    backgroundColor: "#26303A",
    marginVertical: 17,
  },

  aiStats: {
    flexDirection: "row",
    justifyContent: "space-between",
  },

  aiStat: {
    flex: 1,
  },

  statLabel: {
    color: "#697582",
    fontSize: 10,
  },

  statValue: {
    color: "#E6EBF0",
    fontSize: 18,
    fontWeight: "700",
    marginTop: 5,
  },

  statUnit: {
    color: "#5E6874",
    fontSize: 9,
    marginTop: 2,
  },

  completionRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },

  completionBox: {
    flex: 1,
  },

  completionDate: {
    color: "#E6EBF0",
    fontSize: 12,
    fontWeight: "600",
    marginTop: 5,
  },

  sectionTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12,
  },

  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },

  viewAll: {
    color: "#6FC5FF",
    fontSize: 11,
  },

  quickGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: 28,
  },

  actionCard: {
    width: "48%",
    backgroundColor: "#171A20",
    borderRadius: 17,
    padding: 16,
    marginBottom: 10,
  },

  pressed: {
    opacity: 0.7,
    transform: [{ scale: 0.98 }],
  },

  actionIcon: {
    color: "#6FC5FF",
    fontSize: 21,
    marginBottom: 13,
  },

  actionTitle: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },

  actionSubtitle: {
    color: "#737E8A",
    fontSize: 10,
    marginTop: 4,
  },

  unitCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 17,
    marginBottom: 12,
  },

  unitHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },

  unitName: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
    flex: 1,
    paddingRight: 10,
  },

  unitProgress: {
    color: "#6FC5FF",
    fontSize: 12,
    fontWeight: "700",
  },

  unitProgressTrack: {
    height: 5,
    backgroundColor: "#292E36",
    borderRadius: 3,
    marginTop: 10,
    marginBottom: 8,
    overflow: "hidden",
  },

  unitProgressFill: {
    height: "100%",
    backgroundColor: "#6FC5FF",
    borderRadius: 3,
  },

  topicRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
  },

  topicDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginRight: 11,
  },

  completedDot: {
    backgroundColor: "#72D6A0",
  },

  pendingDot: {
    backgroundColor: "#4E5966",
  },

  topicText: {
    color: "#CBD2D9",
    fontSize: 12,
    flex: 1,
  },

  completedTopic: {
    color: "#8F9AA6",
  },

  check: {
    color: "#72D6A0",
    fontSize: 12,
  },

  attendanceCard: {
    backgroundColor: "#171A20",
    borderRadius: 19,
    padding: 20,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 28,
  },

  attendanceLabel: {
    color: "#7B8692",
    fontSize: 12,
  },

  attendanceValue: {
    color: "#FFFFFF",
    fontSize: 30,
    fontWeight: "700",
    marginTop: 6,
  },

  attendanceSecondary: {
    color: "#66717D",
    fontSize: 15,
    fontWeight: "500",
  },

  attendanceRight: {
    alignItems: "flex-end",
  },

  attendancePercent: {
    color: "#72D6A0",
    fontSize: 24,
    fontWeight: "700",
  },

  attendanceSubtext: {
    color: "#66717D",
    fontSize: 10,
    marginTop: 2,
  },

  lectureCard: {
    backgroundColor: "#171A20",
    borderRadius: 17,
    padding: 15,
    flexDirection: "row",
    marginBottom: 10,
  },

  lectureDate: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: "#232832",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },

  lectureDateText: {
    color: "#6FC5FF",
    fontSize: 13,
    fontWeight: "700",
  },

  lectureInfo: {
    flex: 1,
  },

  lectureDateFull: {
    color: "#7A8490",
    fontSize: 10,
  },

  lectureDescription: {
    color: "#E1E6EB",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },

  lectureDuration: {
    color: "#5E6874",
    fontSize: 10,
    marginTop: 5,
  },

  askCard: {
    backgroundColor: "#121820",
    borderRadius: 19,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    marginTop: 18,
    borderWidth: 1,
    borderColor: "#1E2A35",
  },

  askIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: "#1D2B37",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  askIconText: {
    color: "#6FC5FF",
    fontSize: 20,
  },

  askContent: {
    flex: 1,
  },

  askTitle: {
    color: "#E7EBF0",
    fontSize: 13,
    fontWeight: "700",
  },

  askSubtitle: {
    color: "#73808D",
    fontSize: 10,
    lineHeight: 16,
    marginTop: 4,
  },

  askArrow: {
    color: "#65717E",
    fontSize: 27,
    marginLeft: 8,
  },

});