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

import BottomNav
  from "../components/BottomNav";

import {
  getAcademicContext,
  getMe,
  AcademicContext,
} from "../services/api";

export default function HomeScreen() {
  const router = useRouter();

  const [context, setContext] =
    useState<AcademicContext | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    loadHome();
  }, []);

  async function loadHome() {
    try {
      setLoading(true);
      setError("");

      const me = await getMe();

      const data =
        await getAcademicContext(
          me.lecturer_id
        );

      setContext(data);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Couldn&apos;t load dashboard."
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
            Loading dashboard...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !context) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>
            Dashboard unavailable
          </Text>

          <Text style={styles.errorText}>
            {error ||
              "No academic data found."}
          </Text>

          <Pressable
            style={styles.retryButton}
            onPress={loadHome}
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
        style={styles.scroll}
        contentContainerStyle={
          styles.container
        }
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>
              Good evening,
            </Text>

            <Text style={styles.name}>
              {context.lecturer.name} 👋
            </Text>
          </View>

          <Pressable
            style={styles.avatar}
            onPress={() =>
              router.push("/profile")
            }
          >
            <Text style={styles.avatarText}>
              {context.lecturer.name
                .split(" ")
                .map((x) => x[0])
                .join("")
                .slice(0, 2)}
            </Text>
          </Pressable>
        </View>

        <Pressable
          style={styles.nextCard}
          onPress={() =>
            router.push("/schedule")
          }
        >
          <Text style={styles.label}>
            NEXT CLASS
          </Text>

          {context.next_class ? (
            <>
              <Text style={styles.course}>
                {context.next_class.subject}
              </Text>

              <Text style={styles.batch}>
                {context.next_class.code
                  ? `${context.next_class.code} · ${context.next_class.batch}`
                  : context.next_class.batch}
              </Text>

              <View
                style={styles.details}
              >
                <Text style={styles.detail}>
                  {context.next_class.time}{" "}
                  {context.next_class.period}
                </Text>

                <Text style={styles.dot}>
                  •
                </Text>

                <Text style={styles.detail}>
                  {context.next_class.room}
                </Text>
              </View>
            </>
          ) : (
            <Text style={styles.emptyText}>
              No upcoming class.
            </Text>
          )}

          <Text style={styles.tap}>
            Tap to view schedule →
          </Text>
        </Pressable>

        <View style={styles.insightCard}>
          <Text style={styles.insightLabel}>
            PROFPILOT INSIGHT
          </Text>

          <Text style={styles.insightText}>
            {context.alerts.length > 0
              ? context.alerts[0]
              : "No urgent academic alerts right now."}
          </Text>

          <Pressable
            style={styles.aiButton}
            onPress={() =>
              router.push({
                pathname: "/ai",
                params: {
                  course_id:
                    context.selected_course
                      ?.id || "",
                },
              })
            }
          >
            <Text style={styles.aiButtonText}>
              Ask ProfPilot
            </Text>
          </Pressable>
        </View>

        <Text style={styles.sectionTitle}>
          Today&apos;s Schedule
        </Text>

        <View style={styles.schedule}>
          {context.today_schedule.length ===
          0 ? (
            <Text style={styles.emptySchedule}>
              No classes scheduled today.
            </Text>
          ) : (
            context.today_schedule.map(
              (item) => (
                <View
                  key={item.id}
                  style={styles.scheduleRow}
                >
                  <View
                    style={styles.timeBox}
                  >
                    <Text style={styles.time}>
                      {item.time}
                    </Text>

                    <Text style={styles.period}>
                      {item.period}
                    </Text>
                  </View>

                  <View
                    style={styles.scheduleInfo}
                  >
                    <Text
                      style={
                        styles.subject
                      }
                    >
                      {item.subject}
                    </Text>

                    <Text
                      style={styles.batch}
                    >
                      {item.batch}
                    </Text>
                  </View>
                </View>
              )
            )
          )}
        </View>

        <Text style={styles.sectionTitle}>
          Quick Actions
        </Text>

        <View style={styles.grid}>
          <QuickAction
            icon="📚"
            title="Courses"
            onPress={() =>
              router.push(
                "/courses"
              )
            }
          />

          <QuickAction
            icon="📅"
            title="Schedule"
            onPress={() =>
              router.push(
                "/schedule"
              )
            }
          />

          <QuickAction
            icon="✅"
            title="Attendance"
            onPress={() =>
              router.push(
                "/attendance"
              )
            }
          />

          <QuickAction
            icon="👥"
            title="Community"
            onPress={() =>
              router.push(
                "/community"
              )
            }
          />

          <QuickAction
            icon="⚠️"
            title="Risk Radar"
            onPress={() =>
              router.push("/risk")
            }
          />
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>

      <BottomNav />
    </View>
  );
}

function QuickAction({
  icon,
  title,
  onPress,
}: {
  icon: string;
  title: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.action,
        pressed &&
          styles.buttonPressed,
      ]}
      onPress={onPress}
    >
      <Text style={styles.actionIcon}>
        {icon}
      </Text>

      <Text style={styles.actionTitle}>
        {title}
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

    scroll: {
      flex: 1,
    },

    container: {
      padding: 20,
      paddingTop: 60,
    },

    center: {
      flex: 1,
      justifyContent: "center",
      alignItems: "center",
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

    retryButton: {
      backgroundColor: "#FFFFFF",
      paddingHorizontal: 18,
      paddingVertical: 10,
      borderRadius: 10,
      marginTop: 20,
    },

    retryText: {
      color: "#0B0D10",
      fontWeight: "700",
    },

    header: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: 25,
    },

    greeting: {
      color: "#8B919C",
      fontSize: 15,
    },

    name: {
      color: "#FFFFFF",
      fontSize: 25,
      fontWeight: "700",
      marginTop: 3,
    },

    avatar: {
      width: 48,
      height: 48,
      borderRadius: 24,
      backgroundColor: "#252A33",
      alignItems: "center",
      justifyContent: "center",
    },

    avatarText: {
      color: "#FFFFFF",
      fontWeight: "700",
    },

    nextCard: {
      backgroundColor: "#171A20",
      borderRadius: 22,
      padding: 20,
      marginBottom: 16,
    },

    label: {
      color: "#6FC5FF",
      fontSize: 11,
      fontWeight: "700",
      letterSpacing: 1.2,
    },

    course: {
      color: "#FFFFFF",
      fontSize: 21,
      fontWeight: "700",
      marginTop: 10,
    },

    batch: {
      color: "#8C97A3",
      fontSize: 12,
      marginTop: 5,
    },

    details: {
      flexDirection: "row",
      alignItems: "center",
      marginTop: 16,
    },

    detail: {
      color: "#D8DCE2",
      fontSize: 14,
    },

    dot: {
      color: "#5F6772",
      marginHorizontal: 8,
    },

    tap: {
      color: "#65707E",
      fontSize: 11,
      marginTop: 14,
    },

    insightCard: {
      backgroundColor: "#121820",
      borderRadius: 20,
      padding: 20,
      marginBottom: 28,
    },

    insightLabel: {
      color: "#6FC5FF",
      fontSize: 11,
      fontWeight: "700",
      letterSpacing: 1,
    },

    insightText: {
      color: "#E7EBF0",
      fontSize: 15,
      lineHeight: 23,
      marginTop: 10,
    },

    aiButton: {
      marginTop: 17,
      backgroundColor: "#FFFFFF",
      borderRadius: 12,
      paddingVertical: 13,
      alignItems: "center",
    },

    aiButtonText: {
      color: "#0B0D10",
      fontWeight: "700",
    },

    sectionTitle: {
      color: "#FFFFFF",
      fontSize: 18,
      fontWeight: "700",
      marginBottom: 12,
    },

    schedule: {
      backgroundColor: "#171A20",
      borderRadius: 20,
      paddingHorizontal: 18,
      marginBottom: 28,
    },

    scheduleRow: {
      flexDirection: "row",
      paddingVertical: 16,
      borderBottomWidth: 1,
      borderBottomColor: "#252A31",
    },

    timeBox: {
      width: 65,
    },

    time: {
      color: "#FFFFFF",
      fontSize: 15,
      fontWeight: "700",
    },

    period: {
      color: "#69747F",
      fontSize: 10,
    },

    scheduleInfo: {
      flex: 1,
    },

    subject: {
      color: "#E7EBF0",
      fontSize: 14,
      fontWeight: "600",
    },

    emptyText: {
      color: "#7E8794",
      marginTop: 12,
    },

    emptySchedule: {
      color: "#7E8794",
      paddingVertical: 20,
    },

    grid: {
      flexDirection: "row",
      flexWrap: "wrap",
      justifyContent: "space-between",
    },

    action: {
      width: "48%",
      backgroundColor: "#171A20",
      borderRadius: 17,
      padding: 18,
      marginBottom: 12,
    },

    actionIcon: {
      fontSize: 22,
      marginBottom: 10,
    },

    actionTitle: {
      color: "#FFFFFF",
      fontWeight: "600",
    },

    buttonPressed: {
      opacity: 0.7,
      transform: [
        { scale: 0.98 },
      ],
    },
  });