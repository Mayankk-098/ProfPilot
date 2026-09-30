import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useRouter } from "expo-router";
import { useEffect, useState } from "react";

import BottomNav from "../components/BottomNav";
import {
  getSchedule,
  ScheduleItem,
} from "../services/api";

export default function ScheduleScreen() {
  const router = useRouter();

  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadSchedule();
  }, []);

  async function loadSchedule() {
    try {
      setLoading(true);
      setError("");

      const data = await getSchedule();

      setSchedule(data);
    } catch (err) {
      console.error(err);

      setError(
        "Couldn't load your schedule. Make sure the ProfPilot server is running."
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
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>‹</Text>
        </Pressable>

        <Text style={styles.title}>
          Today's Schedule
        </Text>

        <Text style={styles.subtitle}>
          Your academic schedule
        </Text>

        {loading && (
          <View style={styles.stateCard}>
            <ActivityIndicator
              color="#6FC5FF"
            />

            <Text style={styles.stateText}>
              Loading schedule...
            </Text>
          </View>
        )}

        {!loading && error !== "" && (
          <View style={styles.stateCard}>
            <Text style={styles.errorText}>
              {error}
            </Text>

            <Pressable
              style={styles.retryButton}
              onPress={loadSchedule}
            >
              <Text style={styles.retryText}>
                Retry
              </Text>
            </Pressable>
          </View>
        )}

        {!loading &&
          error === "" &&
          schedule.map((item) => (
            <ScheduleCard
              key={item.id}
              item={item}
            />
          ))}

        {!loading &&
          error === "" &&
          schedule.length === 0 && (
            <View style={styles.stateCard}>
              <Text style={styles.stateText}>
                No classes scheduled.
              </Text>
            </View>
          )}
      </ScrollView>

      <BottomNav />
    </View>
  );
}

function ScheduleCard({
  item,
}: {
  item: ScheduleItem;
}) {
  const isMeeting = item.item_type === "meeting";

  return (
    <View
      style={[
        styles.card,
        isMeeting && styles.meetingCard,
      ]}
    >
      <View style={styles.timeBox}>
        <Text style={styles.time}>
          {item.time}
        </Text>

        <Text style={styles.period}>
          {item.period}
        </Text>
      </View>

      <View style={styles.info}>
        <View style={styles.typeBadge}>
          <Text style={styles.typeText}>
            {isMeeting ? "MEETING" : "CLASS"}
          </Text>
        </View>

        <Text style={styles.subject}>
          {item.subject}
        </Text>

        {item.code && (
          <Text style={styles.code}>
            {item.code} · {item.batch}
          </Text>
        )}

        {!item.code && (
          <Text style={styles.code}>
            {item.batch}
          </Text>
        )}

        <Text style={styles.room}>
          {item.room}
        </Text>
      </View>
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
    alignItems: "center",
  },

  stateText: {
    color: "#7E8794",
    fontSize: 13,
    marginTop: 10,
  },

  errorText: {
    color: "#FF9B9B",
    fontSize: 13,
    textAlign: "center",
    lineHeight: 19,
  },

  retryButton: {
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 10,
    marginTop: 14,
  },

  retryText: {
    color: "#0B0D10",
    fontSize: 12,
    fontWeight: "700",
  },

  card: {
    backgroundColor: "#171A20",
    borderRadius: 20,
    padding: 18,
    flexDirection: "row",
    marginBottom: 12,
  },

  meetingCard: {
    backgroundColor: "#141B20",
    borderWidth: 1,
    borderColor: "#25313A",
  },

  timeBox: {
    width: 68,
    paddingTop: 2,
  },

  time: {
    color: "#FFFFFF",
    fontSize: 17,
    fontWeight: "700",
  },

  period: {
    color: "#69747F",
    fontSize: 10,
    marginTop: 2,
  },

  info: {
    flex: 1,
  },

  typeBadge: {
    alignSelf: "flex-start",
    backgroundColor: "#232832",
    borderRadius: 7,
    paddingHorizontal: 7,
    paddingVertical: 4,
    marginBottom: 8,
  },

  typeText: {
    color: "#6FC5FF",
    fontSize: 8,
    fontWeight: "800",
    letterSpacing: 0.8,
  },

  subject: {
    color: "#FFFFFF",
    fontSize: 17,
    lineHeight: 22,
    fontWeight: "700",
  },

  code: {
    color: "#8A95A1",
    fontSize: 12,
    marginTop: 5,
  },

  room: {
    color: "#606B77",
    fontSize: 11,
    marginTop: 11,
  },
});