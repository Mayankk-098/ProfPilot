import BottomNav from "../components/BottomNav";
import {
  getCourses,
  CourseSummary,
} from "../services/api";

import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useRouter } from "expo-router";
import { useEffect, useState } from "react";

export default function CoursesScreen() {
  const router = useRouter();

  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadCourses();
  }, []);

  async function loadCourses() {
    try {
      setLoading(true);
      setError("");

      const data = await getCourses();

      setCourses(data);
    } catch (err) {
      console.error(err);

      setError(
        "Couldn't load courses. Make sure the ProfPilot server is running."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.screen}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={[
          styles.container,
          { paddingBottom: 120 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Back */}
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>‹</Text>
        </Pressable>

        {/* Header */}
        <Text style={styles.title}>
          My Courses
        </Text>

        <Text style={styles.subtitle}>
          Your active courses this semester
        </Text>

        {/* Loading */}
        {loading && (
          <View style={styles.stateCard}>
            <Text style={styles.stateText}>
              Loading courses...
            </Text>
          </View>
        )}

        {/* Error */}
        {!loading && error !== "" && (
          <View style={styles.stateCard}>
            <Text style={styles.errorText}>
              {error}
            </Text>

            <Pressable
              style={styles.retryButton}
              onPress={loadCourses}
            >
              <Text style={styles.retryText}>
                Retry
              </Text>
            </Pressable>
          </View>
        )}

        {/* Courses */}
        {!loading &&
          error === "" &&
          courses.map((course) => (
            <Course
              key={course.id}
              course={course}
              onPress={() =>
                router.push(
                  `/courses/${course.id}`
                )
              }
            />
          ))}

        {/* Add course */}
        {!loading && error === "" && (
          <Pressable style={styles.addCourse}>
            <Text style={styles.addIcon}>+</Text>

            <View>
              <Text style={styles.addTitle}>
                Add a course
              </Text>

              <Text style={styles.addSubtitle}>
                Create another teaching workspace
              </Text>
            </View>
          </Pressable>
        )}
      </ScrollView>

      <BottomNav />
    </View>
  );
}


function Course({
  course,
  onPress,
}: {
  course: CourseSummary;
  onPress: () => void;
}) {
  const isBehind =
    course.progress <
    course.planned_progress;

  return (
    <Pressable
      style={({ pressed }) => [
        styles.card,
        pressed && styles.pressed,
      ]}
      onPress={onPress}
    >
      <View style={styles.cardTop}>
        <View style={styles.courseIcon}>
          <Text style={styles.courseIconText}>
            {course.short_name}
          </Text>
        </View>

        <View style={styles.courseMain}>
          <Text style={styles.name}>
            {course.name}
          </Text>

          <Text style={styles.code}>
            {course.code} · {course.section}
          </Text>
        </View>

        <Text style={styles.chevron}>
          ›
        </Text>
      </View>

      <View style={styles.progressHeader}>
        <Text style={styles.progressLabel}>
          Syllabus progress
        </Text>

        <Text style={styles.progress}>
          {course.progress}%
        </Text>
      </View>

      <View style={styles.progressTrack}>
        <View
          style={[
            styles.progressFill,
            {
              width: `${course.progress}%`,
            },
          ]}
        />
      </View>

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
            styles.status,
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
    </Pressable>
  );
}


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
  },

  backButton: {
    alignSelf: "flex-start",
    paddingVertical: 2,
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
    fontSize: 14,
    marginTop: 5,
    marginBottom: 28,
  },

  stateCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 20,
    marginBottom: 15,
  },

  stateText: {
    color: "#8D98A4",
    fontSize: 13,
  },

  errorText: {
    color: "#FF9B9B",
    fontSize: 13,
    lineHeight: 19,
  },

  retryButton: {
    marginTop: 15,
    alignSelf: "flex-start",
    backgroundColor: "#FFFFFF",
    borderRadius: 10,
    paddingVertical: 9,
    paddingHorizontal: 15,
  },

  retryText: {
    color: "#0B0D10",
    fontSize: 12,
    fontWeight: "700",
  },

  card: {
    backgroundColor: "#171A20",
    borderRadius: 20,
    padding: 20,
    marginBottom: 14,
  },

  pressed: {
    opacity: 0.75,
    transform: [{ scale: 0.99 }],
  },

  cardTop: {
    flexDirection: "row",
    alignItems: "center",
  },

  courseIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: "#232832",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 13,
  },

  courseIconText: {
    color: "#6FC5FF",
    fontSize: 11,
    fontWeight: "800",
  },

  courseMain: {
    flex: 1,
  },

  name: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    lineHeight: 23,
  },

  code: {
    color: "#7E8794",
    fontSize: 12,
    marginTop: 5,
  },

  chevron: {
    color: "#68727D",
    fontSize: 28,
    marginLeft: 8,
  },

  progressHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 24,
  },

  progressLabel: {
    color: "#89939F",
    fontSize: 12,
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

  statusContainer: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    marginTop: 14,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 7,
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

  status: {
    fontSize: 12,
    fontWeight: "600",
  },

  warningText: {
    color: "#FFB86B",
  },

  normalText: {
    color: "#72D6A0",
  },

  addCourse: {
    backgroundColor: "#121820",
    borderRadius: 18,
    padding: 18,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#252A31",
    borderStyle: "dashed",
    marginTop: 4,
  },

  addIcon: {
    color: "#6FC5FF",
    fontSize: 27,
    fontWeight: "300",
    marginRight: 14,
  },

  addTitle: {
    color: "#E4E8ED",
    fontSize: 14,
    fontWeight: "600",
  },

  addSubtitle: {
    color: "#68727D",
    fontSize: 11,
    marginTop: 3,
  },
});