import BottomNav from "../components/BottomNav";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import type { ReactNode } from "react";

export default function ProfileScreen() {
  const router = useRouter();

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

        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>DS</Text>
          </View>

          <Text style={styles.name}>Dr. Sharma</Text>

          <Text style={styles.role}>
            Assistant Professor
          </Text>

          <Text style={styles.department}>
            Computer Science & Engineering
          </Text>

          <View style={styles.onlineBadge}>
            <View style={styles.onlineDot} />
            <Text style={styles.onlineText}>
              Faculty account
            </Text>
          </View>
        </View>

        {/* Stats */}
        <View style={styles.statsCard}>
          <Stat value="2" label="Courses" />
          <Stat value="17" label="Posts" />
          <Stat value="24" label="Resources" />
          <Stat value="42" label="Connections" />
        </View>

        {/* Teaching */}
        <Section title="Teaching">
          <InfoRow
            label="Courses"
            value="DBMS, Artificial Intelligence"
          />

          <InfoRow
            label="Sections"
            value="CSE-A, CSE-B"
          />

          <InfoRow
            label="Experience"
            value="8 Years"
          />
        </Section>

        {/* Research */}
        <Section title="Research Interests">
          <View style={styles.tagRow}>
            <Tag text="Machine Learning" />
            <Tag text="Computer Vision" />
            <Tag text="Artificial Intelligence" />
            <Tag text="Data Science" />
          </View>
        </Section>

        {/* Community */}
        <Section title="Community Activity">
          <InfoRow
            label="Posts"
            value="17"
          />

          <InfoRow
            label="Resources shared"
            value="24"
          />

          <InfoRow
            label="Connections"
            value="42"
          />
        </Section>

        {/* Settings */}
        <Section title="Account">
          <Pressable style={styles.actionRow}>
            <View>
              <Text style={styles.actionTitle}>
                Edit Profile
              </Text>

              <Text style={styles.actionSubtitle}>
                Update your faculty information
              </Text>
            </View>

            <Text style={styles.arrow}>›</Text>
          </Pressable>

          <Pressable style={styles.actionRow}>
            <View>
              <Text style={styles.actionTitle}>
                Notification Preferences
              </Text>

              <Text style={styles.actionSubtitle}>
                Manage class reminders and alerts
              </Text>
            </View>

            <Text style={styles.arrow}>›</Text>
          </Pressable>

          <Pressable
            style={styles.actionRow}
            onPress={() => router.replace("/")}
          >
            <View>
              <Text style={styles.logoutTitle}>
                Sign Out
              </Text>

              <Text style={styles.actionSubtitle}>
                Return to the login screen
              </Text>
            </View>

            <Text style={styles.arrow}>›</Text>
          </Pressable>
        </Section>

        <View style={{ height: 30 }} />
      </ScrollView>

      <BottomNav />
    </View>
  );
}

function Stat({
  value,
  label,
}: {
  value: string;
  label: string;
}) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>

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
      <Text style={styles.label}>{label}</Text>

      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

function Tag({ text }: { text: string }) {
  return (
    <View style={styles.tag}>
      <Text style={styles.tagText}>{text}</Text>
    </View>
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

  profileHeader: {
    alignItems: "center",
    marginBottom: 28,
  },

  avatar: {
    width: 92,
    height: 92,
    borderRadius: 46,
    backgroundColor: "#252A33",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#303740",
  },

  avatarText: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "700",
  },

  name: {
    color: "#FFFFFF",
    fontSize: 27,
    fontWeight: "700",
  },

  role: {
    color: "#C2C9D1",
    fontSize: 14,
    marginTop: 6,
  },

  department: {
    color: "#77828F",
    fontSize: 12,
    textAlign: "center",
    marginTop: 3,
  },

  onlineBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#15231E",
    paddingVertical: 7,
    paddingHorizontal: 10,
    borderRadius: 10,
    marginTop: 12,
  },

  onlineDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#72D6A0",
    marginRight: 7,
  },

  onlineText: {
    color: "#72D6A0",
    fontSize: 11,
    fontWeight: "600",
  },

  statsCard: {
    backgroundColor: "#171A20",
    borderRadius: 19,
    paddingVertical: 19,
    flexDirection: "row",
    justifyContent: "space-around",
    marginBottom: 28,
  },

  stat: {
    alignItems: "center",
  },

  statValue: {
    color: "#FFFFFF",
    fontSize: 19,
    fontWeight: "700",
  },

  statLabel: {
    color: "#737D89",
    fontSize: 10,
    marginTop: 4,
  },

  section: {
    marginBottom: 25,
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
    paddingVertical: 17,
    borderBottomWidth: 1,
    borderBottomColor: "#252A31",
  },

  label: {
    color: "#7E8794",
    fontSize: 12,
    marginBottom: 4,
  },

  value: {
    color: "#E8ECF1",
    fontSize: 15,
  },

  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    paddingVertical: 17,
  },

  tag: {
    backgroundColor: "#232832",
    borderRadius: 12,
    paddingHorizontal: 13,
    paddingVertical: 9,
  },

  tagText: {
    color: "#AEB7C2",
    fontSize: 12,
  },

  actionRow: {
    minHeight: 70,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: "#252A31",
    flexDirection: "row",
    alignItems: "center",
  },

  actionTitle: {
    color: "#E8ECF1",
    fontSize: 14,
    fontWeight: "600",
  },

  logoutTitle: {
    color: "#FF8E8E",
    fontSize: 14,
    fontWeight: "600",
  },

  actionSubtitle: {
    color: "#707B87",
    fontSize: 11,
    marginTop: 4,
  },

  arrow: {
    color: "#68727D",
    fontSize: 27,
    marginLeft: "auto",
  },
});