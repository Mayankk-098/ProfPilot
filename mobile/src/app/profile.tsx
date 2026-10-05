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
  clearAccessToken,
  getAcademicContext,
  getMe,
  CurrentUser,
  AcademicContext,
} from "../services/api";

export default function ProfileScreen() {
  const router = useRouter();

  const [user, setUser] =
    useState<CurrentUser | null>(
      null
    );

  const [context, setContext] =
    useState<AcademicContext | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    try {
      setLoading(true);
      setError("");

      const me = await getMe();

      const data =
        await getAcademicContext(
          me.lecturer_id
        );

      setUser(me);
      setContext(data);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load profile."
      );
    } finally {
      setLoading(false);
    }
  }

  function signOut() {
    clearAccessToken();

    router.replace("/" as any);
  }

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator
            color="#6FC5FF"
          />

          <Text style={styles.stateText}>
            Loading profile...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !context || !user) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>
            Profile unavailable
          </Text>

          <Text style={styles.errorText}>
            {error ||
              "Couldn't load profile data."}
          </Text>

          <Pressable
            style={styles.retry}
            onPress={loadProfile}
          >
            <Text style={styles.retryText}>
              Retry
            </Text>
          </Pressable>
        </View>
      </View>
    );
  }

  const lecturer =
    context.lecturer;

  const initials =
    lecturer.name
      .split(" ")
      .map(
        (part) => part[0]
      )
      .join("")
      .slice(0, 2);

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={
          styles.container
        }
        showsVerticalScrollIndicator={
          false
        }
      >
        <Pressable
          onPress={() => router.back()}
        >
          <Text style={styles.back}>
            ‹
          </Text>
        </Pressable>

        {/* PROFILE HEADER */}

        <View style={styles.header}>
          <View style={styles.avatar}>
            <Text
              style={styles.avatarText}
            >
              {initials}
            </Text>
          </View>

          <Text style={styles.name}>
            {lecturer.name}
          </Text>

          <Text style={styles.role}>
            {lecturer.title}
          </Text>

          <Text
            style={styles.department}
          >
            {lecturer.department}
          </Text>
        </View>

        {/* ACCOUNT */}

        <Section title="Account">
          <InfoRow
            label="Email"
            value={user.email}
          />

          <InfoRow
            label="Lecturer ID"
            value={lecturer.id}
          />
        </Section>

        {/* COURSES */}

        <Section title="Teaching">
          <InfoRow
            label="Active courses"
            value={String(
              context.courses.length
            )}
          />

          <InfoRow
            label="Courses"
            value={
              context.courses.length > 0
                ? context.courses
                    .map(
                      (course) =>
                        course.short_name ||
                        course.code
                    )
                    .join(", ")
                : "No active courses"
            }
          />
        </Section>

        {/* RESEARCH */}

        <Section title="Academic Overview">
          <InfoRow
            label="Current date"
            value={
              context.current_date
            }
          />

          <InfoRow
            label="Upcoming class"
            value={
              context.next_class
                ? context.next_class
                    .subject
                : "No upcoming class"
            }
          />

          <InfoRow
            label="Alerts"
            value={String(
              context.alerts.length
            )}
          />
        </Section>

        {/* SIGN OUT */}

        <Pressable
          style={styles.logout}
          onPress={signOut}
        >
          <Text
            style={styles.logoutTitle}
          >
            Sign Out
          </Text>

          <Text
            style={styles.logoutSubtitle}
          >
            Return to the login screen
          </Text>
        </Pressable>

        <View
          style={{ height: 110 }}
        />
      </ScrollView>

      <BottomNav />
    </View>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text
        style={styles.sectionTitle}
      >
        {title}
      </Text>

      <View style={styles.card}>
        {children}
      </View>
    </View>
  );
}

function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.label}>
        {label}
      </Text>

      <Text style={styles.value}>
        {value}
      </Text>
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
      paddingHorizontal: 20,
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
      marginTop: 10,
    },

    errorTitle: {
      color: "#FFFFFF",
      fontSize: 20,
      fontWeight: "700",
    },

    errorText: {
      color: "#7E8794",
      textAlign: "center",
      marginTop: 8,
    },

    retry: {
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

    back: {
      color: "#FFFFFF",
      fontSize: 38,
      lineHeight: 38,
    },

    header: {
      alignItems: "center",
      marginTop: 12,
      marginBottom: 30,
    },

    avatar: {
      width: 88,
      height: 88,
      borderRadius: 44,
      backgroundColor: "#252A33",
      justifyContent: "center",
      alignItems: "center",
      borderWidth: 1,
      borderColor: "#303740",
    },

    avatarText: {
      color: "#FFFFFF",
      fontSize: 26,
      fontWeight: "700",
    },

    name: {
      color: "#FFFFFF",
      fontSize: 26,
      fontWeight: "700",
      marginTop: 15,
    },

    role: {
      color: "#6FC5FF",
      fontSize: 13,
      marginTop: 5,
    },

    department: {
      color: "#77828F",
      fontSize: 11,
      marginTop: 4,
      textAlign: "center",
    },

    section: {
      marginBottom: 24,
    },

    sectionTitle: {
      color: "#FFFFFF",
      fontSize: 18,
      fontWeight: "700",
      marginBottom: 10,
    },

    card: {
      backgroundColor: "#171A20",
      borderRadius: 18,
      paddingHorizontal: 17,
    },

    infoRow: {
      paddingVertical: 16,
      borderBottomWidth: 1,
      borderBottomColor: "#252A31",
    },

    label: {
      color: "#717C88",
      fontSize: 10,
      marginBottom: 5,
    },

    value: {
      color: "#E6EBF0",
      fontSize: 13,
      lineHeight: 19,
    },

    logout: {
      backgroundColor: "#21191A",
      borderWidth: 1,
      borderColor: "#3A2729",
      borderRadius: 17,
      padding: 17,
    },

    logoutTitle: {
      color: "#FF8E8E",
      fontSize: 14,
      fontWeight: "700",
    },

    logoutSubtitle: {
      color: "#816B6D",
      fontSize: 10,
      marginTop: 4,
    },
  });