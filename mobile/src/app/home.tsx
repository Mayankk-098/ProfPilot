import BottomNav from "../components/BottomNav";
import { useRouter } from "expo-router";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

export default function HomeScreen() {
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
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Good evening,</Text>
            <Text style={styles.name}>Dr. Sharma 👋</Text>
          </View>

          <Pressable
            style={styles.avatar}
            onPress={() => router.push("/profile")}
          >
            <Text style={styles.avatarText}>DS</Text>
          </Pressable>
        </View>

        {/* Next Class */}
        <Pressable
          style={styles.nextClassCard}
          onPress={() => router.push("/schedule")}
        >
          <Text style={styles.cardLabel}>NEXT CLASS</Text>

          <Text style={styles.course}>
            Database Management Systems
          </Text>

          <Text style={styles.section}>CSE-B</Text>

          <View style={styles.classDetails}>
            <Text style={styles.detail}>10:00 AM</Text>
            <Text style={styles.dot}>•</Text>
            <Text style={styles.detail}>Block C · Room 204</Text>
          </View>

          <View style={styles.countdown}>
            <Text style={styles.countdownText}>
              Starts in 27 minutes
            </Text>
          </View>

          <Text style={styles.tapHint}>
            Tap to view schedule →
          </Text>
        </Pressable>

        {/* AI Insight */}
        <View style={styles.insightCard}>
          <Text style={styles.insightLabel}>
            PROFPILOT INSIGHT
          </Text>

          <Text style={styles.insightText}>
            Your DBMS syllabus is currently{" "}
            <Text style={styles.highlight}>
              4 days behind
            </Text>{" "}
            the planned pace.
          </Text>

          <Pressable
            style={({ pressed }) => [
              styles.aiButton,
              pressed && styles.buttonPressed,
            ]}
            onPress={() => router.push("/ai")}
          >
            <Text style={styles.aiButtonText}>
              Ask ProfPilot
            </Text>
          </Pressable>
        </View>

        {/* Schedule */}
        <Text style={styles.sectionTitle}>
          Today's Schedule
        </Text>

        <View style={styles.scheduleCard}>
          <ScheduleRow
            time="10:00"
            period="AM"
            subject="DBMS"
            batch="CSE-B"
          />

          <ScheduleRow
            time="12:00"
            period="PM"
            subject="Artificial Intelligence"
            batch="CSE-A"
          />

          <ScheduleRow
            time="03:00"
            period="PM"
            subject="Faculty Meeting"
            batch="Faculty"
          />
        </View>

        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>
          Quick Actions
        </Text>

        <View style={styles.quickActions}>
          <QuickAction
            emoji="📚"
            title="Courses"
            onPress={() => router.push("/courses")}
          />

          <QuickAction
            emoji="📅"
            title="Schedule"
            onPress={() => router.push("/schedule")}
          />

          <QuickAction
            emoji="✅"
            title="Attendance"
            onPress={() => router.push("/attendance")}
          />

          <QuickAction
            emoji="👥"
            title="Community"
            onPress={() => router.push("/community")}
          />
        </View>

        {/* Extra bottom space */}
        <View style={{ height: 30 }} />
      </ScrollView>

      {/* ProfPilot Bottom Navigation */}
      <BottomNav />
    </View>
  );
}

function ScheduleRow({
  time,
  period,
  subject,
  batch,
}: {
  time: string;
  period: string;
  subject: string;
  batch: string;
}) {
  return (
    <View style={styles.scheduleRow}>
      <View style={styles.timeContainer}>
        <Text style={styles.time}>{time}</Text>
        <Text style={styles.period}>{period}</Text>
      </View>

      <View style={styles.scheduleInfo}>
        <Text style={styles.subject}>{subject}</Text>
        <Text style={styles.batch}>{batch}</Text>
      </View>
    </View>
  );
}

function QuickAction({
  emoji,
  title,
  onPress,
}: {
  emoji: string;
  title: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.quickAction,
        pressed && styles.buttonPressed,
      ]}
      onPress={onPress}
    >
      <Text style={styles.quickEmoji}>{emoji}</Text>
      <Text style={styles.quickTitle}>{title}</Text>
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
    paddingTop: 60,
  },

  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 28,
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
    justifyContent: "center",
    alignItems: "center",
  },

  avatarText: {
    color: "#FFFFFF",
    fontWeight: "700",
    fontSize: 15,
  },

  nextClassCard: {
    backgroundColor: "#171A20",
    borderRadius: 22,
    padding: 20,
    marginBottom: 16,
  },

  cardLabel: {
    color: "#7E8794",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
  },

  course: {
    color: "#FFFFFF",
    fontSize: 22,
    fontWeight: "700",
    marginTop: 10,
  },

  section: {
    color: "#9DA6B2",
    fontSize: 14,
    marginTop: 4,
  },

  classDetails: {
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

  countdown: {
    marginTop: 18,
    alignSelf: "flex-start",
    backgroundColor: "#232832",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 10,
  },

  countdownText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },

  tapHint: {
    color: "#65707E",
    fontSize: 12,
    marginTop: 12,
  },

  insightCard: {
    backgroundColor: "#121820",
    borderRadius: 20,
    padding: 20,
    marginBottom: 28,
  },

  insightLabel: {
    color: "#6FC5FF",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1,
  },

  insightText: {
    color: "#E7EBF0",
    fontSize: 16,
    lineHeight: 24,
    marginTop: 10,
  },

  highlight: {
    color: "#6FC5FF",
    fontWeight: "700",
  },

  aiButton: {
    marginTop: 18,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    paddingVertical: 13,
    alignItems: "center",
  },

  buttonPressed: {
    opacity: 0.7,
    transform: [{ scale: 0.98 }],
  },

  aiButtonText: {
    color: "#0B0D10",
    fontWeight: "700",
    fontSize: 14,
  },

  sectionTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12,
  },

  scheduleCard: {
    backgroundColor: "#171A20",
    borderRadius: 20,
    paddingHorizontal: 18,
    marginBottom: 28,
  },

  scheduleRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 17,
    borderBottomWidth: 1,
    borderBottomColor: "#252A31",
  },

  timeContainer: {
    width: 65,
  },

  time: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },

  period: {
    color: "#7E8794",
    fontSize: 11,
    marginTop: 2,
  },

  scheduleInfo: {
    flex: 1,
  },

  subject: {
    color: "#E7EBF0",
    fontSize: 15,
    fontWeight: "600",
  },

  batch: {
    color: "#7E8794",
    fontSize: 12,
    marginTop: 4,
  },

  quickActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },

  quickAction: {
    width: "48%",
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 18,
    marginBottom: 12,
  },

  quickEmoji: {
    fontSize: 23,
    marginBottom: 10,
  },

  quickTitle: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});