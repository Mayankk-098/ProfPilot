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
  getSchedule,
  ScheduleItem,
} from "../services/api";

export default function ScheduleScreen() {
  const router = useRouter();

  const [schedule, setSchedule] =
    useState<ScheduleItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    loadSchedule();
  }, []);

  async function loadSchedule() {
    try {
      setLoading(true);
      setError("");

      const data =
        await getSchedule();

      setSchedule(data);
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load schedule."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={
          styles.container
        }
        showsVerticalScrollIndicator={false}
      >
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>
            ‹
          </Text>
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

        {!loading && error && (
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
          !error &&
          schedule.length === 0 && (
            <View style={styles.stateCard}>
              <Text style={styles.emptyTitle}>
                No classes scheduled
              </Text>

              <Text style={styles.stateText}>
                There are no schedule items available
                for today.
              </Text>
            </View>
          )}

        {!loading &&
          !error &&
          schedule.map((item) => (
            <ScheduleCard
              key={item.id}
              item={item}
            />
          ))}

        <View
          style={{ height: 110 }}
        />
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
  const isMeeting =
    item.item_type ===
    "meeting";

  return (
    <View
      style={[
        styles.card,
        isMeeting &&
          styles.meetingCard,
      ]}
    >
      <View style={styles.timeBox}>
        <Text style={styles.time}>
          {item.time ||
            item.start_time ||
            "--"}
        </Text>

        {item.period && (
          <Text style={styles.period}>
            {item.period}
          </Text>
        )}
      </View>

      <View style={styles.info}>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>
            {isMeeting
              ? "MEETING"
              : "CLASS"}
          </Text>
        </View>

        <Text style={styles.subject}>
          {item.subject}
        </Text>

        <Text style={styles.meta}>
          {item.code
            ? `${item.code} · ${item.batch}`
            : item.batch}
        </Text>

        <Text style={styles.room}>
          {item.room ||
            "Room not assigned"}
        </Text>

        {item.status &&
          item.status !==
            "scheduled" && (
            <Text style={styles.status}>
              {item.status.toUpperCase()}
            </Text>
          )}
      </View>
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
      padding: 20,
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
      marginBottom: 25,
    },

    stateCard: {
      backgroundColor: "#171A20",
      borderRadius: 18,
      padding: 20,
      alignItems: "center",
      marginBottom: 14,
    },

    stateText: {
      color: "#7E8794",
      fontSize: 12,
      textAlign: "center",
      marginTop: 9,
    },

    emptyTitle: {
      color: "#FFFFFF",
      fontSize: 15,
      fontWeight: "700",
    },

    errorText: {
      color: "#FF9B9B",
      fontSize: 12,
      lineHeight: 18,
      textAlign: "center",
    },

    retryButton: {
      backgroundColor: "#FFFFFF",
      paddingHorizontal: 17,
      paddingVertical: 9,
      borderRadius: 10,
      marginTop: 15,
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
      borderWidth: 1,
      borderColor: "#29343D",
      backgroundColor: "#141B20",
    },

    timeBox: {
      width: 70,
      paddingTop: 2,
    },

    time: {
      color: "#FFFFFF",
      fontSize: 16,
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

    badge: {
      alignSelf: "flex-start",
      backgroundColor: "#232832",
      borderRadius: 7,
      paddingHorizontal: 7,
      paddingVertical: 4,
      marginBottom: 8,
    },

    badgeText: {
      color: "#6FC5FF",
      fontSize: 8,
      fontWeight: "800",
      letterSpacing: 0.7,
    },

    subject: {
      color: "#FFFFFF",
      fontSize: 17,
      fontWeight: "700",
      lineHeight: 22,
    },

    meta: {
      color: "#8A95A1",
      fontSize: 11,
      marginTop: 5,
    },

    room: {
      color: "#606B77",
      fontSize: 10,
      marginTop: 10,
    },

    status: {
      color: "#FFB86B",
      fontSize: 9,
      fontWeight: "700",
      marginTop: 8,
    },
  });