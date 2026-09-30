import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

export default function AttendanceScreen() {
  const router = useRouter();

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={styles.container}
        showsVerticalScrollIndicator={false}
      >
        <Pressable onPress={() => router.back()}>
          <Text style={styles.back}>‹</Text>
        </Pressable>

        <Text style={styles.title}>Attendance</Text>
        <Text style={styles.subtitle}>Current semester</Text>

        <View style={styles.summary}>
          <Text style={styles.summaryLabel}>DBMS · CSE-B</Text>
          <Text style={styles.percentage}>78%</Text>
          <Text style={styles.summaryText}>
            56 present · 6 absent
          </Text>
        </View>

        <Text style={styles.sectionTitle}>Low Attendance</Text>

        <Student name="24BCS018" percentage="71%" />
        <Student name="24BCS031" percentage="68%" />
        <Student name="24BCS047" percentage="73%" />

        <Text style={styles.note}>
          Students below 75% are automatically flagged by ProfPilot.
        </Text>
      </ScrollView>
    </View>
  );
}

function Student({
  name,
  percentage,
}: {
  name: string;
  percentage: string;
}) {
  return (
    <View style={styles.student}>
      <View>
        <Text style={styles.studentId}>{name}</Text>
        <Text style={styles.studentWarning}>Below 75%</Text>
      </View>

      <Text style={styles.studentPercentage}>{percentage}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#0B0D10",
  },

  container: {
    padding: 20,
    paddingTop: 55,
  },

  back: {
    color: "#FFFFFF",
    fontSize: 38,
  },

  title: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "700",
  },

  subtitle: {
    color: "#7E8794",
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
    fontSize: 13,
  },

  percentage: {
    color: "#FFFFFF",
    fontSize: 42,
    fontWeight: "700",
    marginTop: 10,
  },

  summaryText: {
    color: "#7E8794",
    marginTop: 5,
  },

  sectionTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12,
  },

  student: {
    backgroundColor: "#171A20",
    borderRadius: 16,
    padding: 17,
    marginBottom: 10,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },

  studentId: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },

  studentWarning: {
    color: "#7E8794",
    fontSize: 12,
    marginTop: 3,
  },

  studentPercentage: {
    color: "#FFB86B",
    fontSize: 17,
    fontWeight: "700",
  },

  note: {
    color: "#626C78",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 15,
  },
});