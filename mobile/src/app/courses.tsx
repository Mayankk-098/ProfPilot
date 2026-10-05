import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  useEffect,
  useState,
} from "react";

import {
  useRouter,
} from "expo-router";

import BottomNav from "../components/BottomNav";

import {
  getCourses,
  CourseSummary,
} from "../services/api";

export default function CoursesScreen() {
  const router = useRouter();

  const [courses, setCourses] =
    useState<CourseSummary[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    loadCourses();
  }, []);

  async function loadCourses() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getCourses();

      setCourses(data);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load courses."
      );
    } finally {
      setLoading(false);
    }
  }

  function openCourse(
    courseId: string
  ) {
    router.push({
      pathname: "/courses/[id]" as any,
      params: {
        id: String(courseId),
      },
    });
  }

  return (
    <View style={styles.screen}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={
          styles.container
        }
        showsVerticalScrollIndicator={
          false
        }
      >
        {/* BACK */}
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>
            ‹
          </Text>
        </Pressable>

        {/* HEADER */}
        <View style={styles.header}>
          <Text style={styles.title}>
            My Courses
          </Text>

          <Text style={styles.subtitle}>
            Your active courses this semester
          </Text>
        </View>

        {/* LOADING */}
        {loading && (
          <View style={styles.stateCard}>
            <ActivityIndicator
              size="small"
              color="#6FC5FF"
            />

            <Text style={styles.stateText}>
              Loading courses...
            </Text>
          </View>
        )}

        {/* ERROR */}
        {!loading &&
          error !== "" && (
            <View
              style={styles.stateCard}
            >
              <Text
                style={styles.errorTitle}
              >
                Couldn't load courses
              </Text>

              <Text
                style={styles.errorText}
              >
                {error}
              </Text>

              <Pressable
                style={styles.retryButton}
                onPress={loadCourses}
              >
                <Text
                  style={styles.retryText}
                >
                  Retry
                </Text>
              </Pressable>
            </View>
          )}

        {/* EMPTY */}
        {!loading &&
          error === "" &&
          courses.length === 0 && (
            <View
              style={styles.stateCard}
            >
              <Text
                style={styles.emptyTitle}
              >
                No courses found
              </Text>

              <Text
                style={styles.stateText}
              >
                No active courses are available
                for your faculty account.
              </Text>
            </View>
          )}

        {/* COURSE LIST */}
        {!loading &&
          error === "" &&
          courses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onPress={() =>
                openCourse(course.id)
              }
            />
          ))}

        {/* INFORMATIONAL FOOTER */}
        {!loading &&
          error === "" &&
          courses.length > 0 && (
            <View
              style={styles.footerCard}
            >
              <Text
                style={styles.footerTitle}
              >
                Course management
              </Text>

              <Text
                style={styles.footerText}
              >
                Courses are managed by the
                current academic backend.
              </Text>
            </View>
          )}

        <View
          style={{ height: 110 }}
        />
      </ScrollView>

      <BottomNav />
    </View>
  );
}

// ==================================================
// COURSE CARD
// ==================================================

function CourseCard({
  course,
  onPress,
}: {
  course: CourseSummary;
  onPress: () => void;
}) {
  const isBehind =
    course.progress <
    course.planned_progress;

  const progress = Math.min(
    100,
    Math.max(0, course.progress)
  );

  return (
    <Pressable
      style={({ pressed }) => [
        styles.card,
        pressed && styles.pressed,
      ]}
      onPress={onPress}
    >
      {/* TOP */}
      <View style={styles.cardTop}>
        <View style={styles.courseIcon}>
          <Text
            style={styles.courseIconText}
            numberOfLines={1}
          >
            {course.short_name ||
              course.code}
          </Text>
        </View>

        <View
          style={styles.courseMain}
        >
          <Text
            style={styles.courseName}
            numberOfLines={2}
          >
            {course.name}
          </Text>

          <Text style={styles.courseCode}>
            {course.code} ·{" "}
            {course.section}
          </Text>
        </View>

        <Text style={styles.chevron}>
          ›
        </Text>
      </View>

      {/* PROGRESS */}
      <View
        style={styles.progressHeader}
      >
        <Text
          style={
            styles.progressLabel
          }
        >
          Syllabus progress
        </Text>

        <Text style={styles.progress}>
          {Math.round(progress)}%
        </Text>
      </View>

      <View
        style={styles.progressTrack}
      >
        <View
          style={[
            styles.progressFill,
            {
              width: `${progress}%`,
            },
          ]}
        />
      </View>

      {/* STATUS */}
      <View
        style={[
          styles.statusContainer,
          isBehind
            ? styles.warningContainer
            : styles.normalContainer,
        ]}
      >
        <View
          style={[
            styles.statusDot,
            isBehind
              ? styles.warningDot
              : styles.normalDot,
          ]}
        />

        <Text
          style={[
            styles.statusText,
            isBehind
              ? styles.warningText
              : styles.normalText,
          ]}
        >
          {isBehind
            ? "Behind planned pace"
            : "On schedule"}
        </Text>
      </View>

      {/* FOOTER */}
      <View style={styles.cardFooter}>
        <Text style={styles.footerMeta}>
          {course.total_students} students
        </Text>

        <Text style={styles.footerMeta}>
          {course.present_today} present today
        </Text>
      </View>
    </Pressable>
  );
}

// ==================================================
// STYLES
// ==================================================

const styles =
  StyleSheet.create({
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
    },

    backButton: {
      alignSelf: "flex-start",
      paddingRight: 15,
      paddingVertical: 2,
    },

    back: {
      color: "#FFFFFF",
      fontSize: 38,
      lineHeight: 38,
    },

    header: {
      marginTop: 8,
      marginBottom: 25,
    },

    title: {
      color: "#FFFFFF",
      fontSize: 28,
      fontWeight: "700",
    },

    subtitle: {
      color: "#7E8794",
      fontSize: 14,
      marginTop: 5,
    },

    // ----------------------------------------------
    // STATES
    // ----------------------------------------------

    stateCard: {
      backgroundColor: "#171A20",
      borderRadius: 18,
      padding: 22,
      alignItems: "center",
      marginBottom: 15,
    },

    stateText: {
      color: "#8D98A4",
      fontSize: 12,
      lineHeight: 18,
      textAlign: "center",
      marginTop: 8,
    },

    emptyTitle: {
      color: "#FFFFFF",
      fontSize: 16,
      fontWeight: "700",
    },

    errorTitle: {
      color: "#FFFFFF",
      fontSize: 16,
      fontWeight: "700",
      textAlign: "center",
    },

    errorText: {
      color: "#FF9B9B",
      fontSize: 12,
      lineHeight: 18,
      textAlign: "center",
      marginTop: 8,
    },

    retryButton: {
      marginTop: 16,
      backgroundColor: "#FFFFFF",
      borderRadius: 10,
      paddingVertical: 10,
      paddingHorizontal: 18,
    },

    retryText: {
      color: "#0B0D10",
      fontSize: 12,
      fontWeight: "700",
    },

    // ----------------------------------------------
    // COURSE CARD
    // ----------------------------------------------

    card: {
      backgroundColor: "#171A20",
      borderRadius: 20,
      padding: 20,
      marginBottom: 14,
    },

    pressed: {
      opacity: 0.75,
      transform: [
        {
          scale: 0.99,
        },
      ],
    },

    cardTop: {
      flexDirection: "row",
      alignItems: "center",
    },

    courseIcon: {
      width: 50,
      height: 50,
      borderRadius: 15,
      backgroundColor: "#232832",
      alignItems: "center",
      justifyContent: "center",
      marginRight: 13,
    },

    courseIconText: {
      color: "#6FC5FF",
      fontSize: 10,
      fontWeight: "800",
      maxWidth: 42,
    },

    courseMain: {
      flex: 1,
    },

    courseName: {
      color: "#FFFFFF",
      fontSize: 17,
      fontWeight: "700",
      lineHeight: 22,
    },

    courseCode: {
      color: "#7E8794",
      fontSize: 11,
      marginTop: 5,
    },

    chevron: {
      color: "#68727D",
      fontSize: 28,
      marginLeft: 8,
    },

    // ----------------------------------------------
    // PROGRESS
    // ----------------------------------------------

    progressHeader: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      marginTop: 24,
    },

    progressLabel: {
      color: "#89939F",
      fontSize: 11,
    },

    progress: {
      color: "#FFFFFF",
      fontSize: 12,
      fontWeight: "700",
    },

    progressTrack: {
      height: 7,
      backgroundColor: "#292E36",
      borderRadius: 5,
      marginTop: 9,
      overflow: "hidden",
    },

    progressFill: {
      height: "100%",
      backgroundColor: "#6FC5FF",
      borderRadius: 5,
    },

    // ----------------------------------------------
    // STATUS
    // ----------------------------------------------

    statusContainer: {
      alignSelf: "flex-start",
      flexDirection: "row",
      alignItems: "center",
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 7,
      marginTop: 14,
    },

    warningContainer: {
      backgroundColor: "#2A211A",
    },

    normalContainer: {
      backgroundColor: "#18241F",
    },

    statusDot: {
      width: 7,
      height: 7,
      borderRadius: 4,
      marginRight: 7,
    },

    warningDot: {
      backgroundColor: "#FFB86B",
    },

    normalDot: {
      backgroundColor: "#72D6A0",
    },

    statusText: {
      fontSize: 11,
      fontWeight: "600",
    },

    warningText: {
      color: "#FFB86B",
    },

    normalText: {
      color: "#72D6A0",
    },

    // ----------------------------------------------
    // CARD FOOTER
    // ----------------------------------------------

    cardFooter: {
      flexDirection: "row",
      justifyContent: "space-between",
      marginTop: 15,
      paddingTop: 12,
      borderTopWidth: 1,
      borderTopColor: "#252A31",
    },

    footerMeta: {
      color: "#65707C",
      fontSize: 10,
    },

    // ----------------------------------------------
    // FOOTER INFO
    // ----------------------------------------------

    footerCard: {
      backgroundColor: "#121820",
      borderWidth: 1,
      borderColor: "#1E2A35",
      borderRadius: 17,
      padding: 17,
      marginTop: 4,
    },

    footerTitle: {
      color: "#E7EBF0",
      fontSize: 13,
      fontWeight: "700",
    },

    footerText: {
      color: "#73808D",
      fontSize: 10,
      lineHeight: 16,
      marginTop: 5,
    },
  });