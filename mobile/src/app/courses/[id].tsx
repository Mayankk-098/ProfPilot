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
  useLocalSearchParams,
  useRouter,
} from "expo-router";

import {
  getCourse,
  CourseDetail,
} from "../../services/api";

export default function CourseDetailScreen() {
  const router = useRouter();

  const { id } =
    useLocalSearchParams<{
      id?: string;
    }>();

  const [course, setCourse] =
    useState<CourseDetail | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    if (id) {
      loadCourse(id);
    }
  }, [id]);

  async function loadCourse(
    courseId: string
  ) {
    try {
      setLoading(true);
      setError("");

      const data =
        await getCourse(courseId);

      setCourse(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load course."
      );
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
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

  if (error || !course) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>
            Course unavailable
          </Text>

          <Text style={styles.errorText}>
            {error ||
              "Course not found."}
          </Text>

          <Pressable
            style={styles.retry}
            onPress={() =>
              id && loadCourse(id)
            }
          >
            <Text style={styles.retryText}>
              Retry
            </Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={
          styles.container
        }
      >
        <Pressable
          onPress={() => router.back()}
        >
          <Text style={styles.back}>
            ‹
          </Text>
        </Pressable>

        <Text style={styles.code}>
          {course.code} ·{" "}
          {course.section}
        </Text>

        <Text style={styles.title}>
          {course.name}
        </Text>

        <Text style={styles.department}>
          {course.department}
        </Text>

        <View style={styles.analysis}>
          <Text style={styles.analysisLabel}>
            PROFPILOT ANALYSIS
          </Text>

          <Text style={styles.analysisTitle}>
            {course.progress <
            course.planned_progress
              ? "Course is behind planned pace"
              : "Course is progressing well"}
          </Text>

          <Text style={styles.analysisText}>
            Current completion:{" "}
            <Text style={styles.highlight}>
              {course.progress}%
            </Text>
          </Text>

          <Text style={styles.analysisText}>
            Planned completion:{" "}
            <Text style={styles.highlight}>
              {course.planned_progress}%
            </Text>
          </Text>
        </View>

        <Text style={styles.sectionTitle}>
          Course Workspace
        </Text>

        <View style={styles.grid}>
          <ActionCard
            icon="✓"
            title="Attendance"
            subtitle={`${course.total_students} students`}
            onPress={() =>
              router.push({
                pathname:
                  "/attendance",
                params: {
                  course_id:
                    course.id,
                },
              })
            }
          />

          <ActionCard
            icon="✦"
            title="AI Insights"
            subtitle="Ask about this course"
            onPress={() =>
              router.push({
                pathname: "/ai",
                params: {
                  course_id:
                    course.id,
                },
              })
            }
          />

          <ActionCard
            icon="◷"
            title="Schedule"
            subtitle="View classes"
            onPress={() =>
              router.push(
                "/schedule"
              )
            }
          />

          <ActionCard
            icon="◎"
            title="Syllabus"
            subtitle="Manage units & topics"
            onPress={() =>
              router.push({
                pathname: "/courses/[id]/syllabus" as any,
                params: { id: course.id },
              })
            }
          />
        </View>

        <Text style={styles.sectionTitle}>
          Syllabus
        </Text>

        {course.syllabus.map(
          (unit) => (
            <View
              key={unit.id}
              style={styles.unit}
            >
              <View
                style={
                  styles.unitHeader
                }
              >
                <Text style={styles.unitName}>
                  {unit.name}
                </Text>

                <Text
                  style={
                    styles.unitPercent
                  }
                >
                  {Math.round(
                    unit.progress
                  )}
                  %
                </Text>
              </View>

              <View
                style={styles.track}
              >
                <View
                  style={[
                    styles.fill,
                    {
                      width: `${Math.min(
                        100,
                        Math.max(
                          0,
                          unit.progress
                        )
                      )}%`,
                    },
                  ]}
                />
              </View>

              {unit.topics.map(
                (topic) => (
                  <View
                    key={topic.id}
                    style={styles.topic}
                  >
                    <Text
                      style={
                        styles.topicDot
                      }
                    >
                      {topic.completed
                        ? "✓"
                        : "•"}
                    </Text>

                    <Text
                      style={[
                        styles.topicText,
                        topic.completed &&
                          styles.completed,
                      ]}
                    >
                      {topic.name}
                    </Text>
                  </View>
                )
              )}
            </View>
          )
        )}

        <Text style={styles.sectionTitle}>
          Recent Lectures
        </Text>

        {course.lectures
          .slice()
          .reverse()
          .slice(0, 5)
          .map((lecture) => (
            <View
              key={lecture.id}
              style={styles.lecture}
            >
              <Text
                style={
                  styles.lectureDate
                }
              >
                {lecture.date}
              </Text>

              <Text
                style={
                  styles.lectureText
                }
              >
                {lecture.description}
              </Text>

              <Text
                style={
                  styles.lectureDuration
                }
              >
                {lecture.duration} minutes
              </Text>
            </View>
          ))}

        <Pressable
          style={styles.ask}
          onPress={() =>
            router.push({
              pathname: "/ai",
              params: {
                course_id:
                  course.id,
              },
            })
          }
        >
          <Text style={styles.askTitle}>
            Ask ProfPilot about this course
          </Text>

          <Text style={styles.askText}>
            Ask about syllabus, lectures,
            attendance and course progress.
          </Text>
        </Pressable>

        <View
          style={{ height: 50 }}
        />
      </ScrollView>
    </View>
  );
}

function ActionCard({
  icon,
  title,
  subtitle,
  onPress,
}: {
  icon: string;
  title: string;
  subtitle: string;
  onPress?: () => void;
}) {
  return (
    <Pressable
      style={styles.action}
      onPress={onPress}
      disabled={!onPress}
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
      marginTop: 10,
    },

    retry: {
      backgroundColor: "#FFFFFF",
      padding: 10,
      paddingHorizontal: 18,
      borderRadius: 10,
      marginTop: 20,
    },

    retryText: {
      color: "#0B0D10",
      fontWeight: "700",
    },

    back: {
      color: "#FFFFFF",
      fontSize: 38,
      marginBottom: 10,
    },

    code: {
      color: "#6FC5FF",
      fontWeight: "700",
      fontSize: 11,
    },

    title: {
      color: "#FFFFFF",
      fontSize: 27,
      fontWeight: "700",
      marginTop: 8,
    },

    department: {
      color: "#75808D",
      marginTop: 6,
    },

    analysis: {
      backgroundColor: "#121820",
      borderRadius: 20,
      padding: 20,
      marginTop: 22,
      marginBottom: 28,
    },

    analysisLabel: {
      color: "#6FC5FF",
      fontSize: 10,
      fontWeight: "700",
    },

    analysisTitle: {
      color: "#FFFFFF",
      fontSize: 17,
      fontWeight: "700",
      marginTop: 9,
    },

    analysisText: {
      color: "#8C97A3",
      fontSize: 13,
      marginTop: 8,
    },

    highlight: {
      color: "#6FC5FF",
      fontWeight: "700",
    },

    sectionTitle: {
      color: "#FFFFFF",
      fontSize: 18,
      fontWeight: "700",
      marginBottom: 12,
      marginTop: 5,
    },

    grid: {
      flexDirection: "row",
      flexWrap: "wrap",
      justifyContent: "space-between",
      marginBottom: 25,
    },

    action: {
      width: "48%",
      backgroundColor: "#171A20",
      borderRadius: 17,
      padding: 16,
      marginBottom: 10,
    },

    actionIcon: {
      color: "#6FC5FF",
      fontSize: 21,
    },

    actionTitle: {
      color: "#FFFFFF",
      fontWeight: "700",
      marginTop: 12,
    },

    actionSubtitle: {
      color: "#737E8A",
      fontSize: 10,
      marginTop: 4,
    },

    unit: {
      backgroundColor: "#171A20",
      borderRadius: 18,
      padding: 17,
      marginBottom: 12,
    },

    unitHeader: {
      flexDirection: "row",
      justifyContent: "space-between",
    },

    unitName: {
      color: "#FFFFFF",
      fontWeight: "700",
      flex: 1,
      paddingRight: 10,
    },

    unitPercent: {
      color: "#6FC5FF",
      fontWeight: "700",
    },

    track: {
      height: 5,
      backgroundColor: "#292E36",
      borderRadius: 3,
      marginTop: 10,
      overflow: "hidden",
    },

    fill: {
      height: "100%",
      backgroundColor: "#6FC5FF",
    },

    topic: {
      flexDirection: "row",
      alignItems: "center",
      marginTop: 10,
    },

    topicDot: {
      color: "#72D6A0",
      width: 20,
    },

    topicText: {
      color: "#CBD2D9",
      flex: 1,
      fontSize: 12,
    },

    completed: {
      color: "#8B95A0",
    },

    lecture: {
      backgroundColor: "#171A20",
      borderRadius: 16,
      padding: 15,
      marginBottom: 10,
    },

    lectureDate: {
      color: "#6FC5FF",
      fontSize: 11,
    },

    lectureText: {
      color: "#DDE2E7",
      marginTop: 5,
    },

    lectureDuration: {
      color: "#66717D",
      fontSize: 10,
      marginTop: 5,
    },

    ask: {
      backgroundColor: "#121820",
      borderRadius: 18,
      padding: 17,
      marginTop: 20,
      borderWidth: 1,
      borderColor: "#1E2A35",
    },

    askTitle: {
      color: "#E7EBF0",
      fontWeight: "700",
    },

    askText: {
      color: "#73808D",
      fontSize: 11,
      lineHeight: 17,
      marginTop: 5,
    },
  });