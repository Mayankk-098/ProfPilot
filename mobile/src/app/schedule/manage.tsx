import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "expo-router";

import {
  CourseSummary,
  ScheduleTemplate,
  createScheduleTemplate,
  deleteScheduleTemplate,
  getCourses,
  getScheduleTemplates,
  updateScheduleTemplate,
} from "../../services/api";

const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

function normalizeTime(value: string) {
  const trimmed = value.trim();

  if (!/^\d{2}:\d{2}$/.test(trimmed)) {
    return null;
  }

  const [hours, minutes] = trimmed.split(":").map(Number);

  if (
    Number.isNaN(hours) ||
    Number.isNaN(minutes) ||
    hours < 0 ||
    hours > 23 ||
    minutes < 0 ||
    minutes > 59
  ) {
    return null;
  }

  return trimmed;
}

export default function TimetableManagerScreen() {
  const router = useRouter();

  const [templates, setTemplates] = useState<ScheduleTemplate[]>([]);
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const [weekday, setWeekday] = useState(0);
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");
  const [room, setRoom] = useState("");
  const [courseId, setCourseId] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const [scheduleData, courseData] = await Promise.all([
        getScheduleTemplates(),
        getCourses(),
      ]);

      setTemplates(scheduleData);
      setCourses(courseData);

      if (!courseId && courseData.length > 0) {
        setCourseId(courseData[0].id);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't load timetable."
      );
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    void Promise.resolve().then(() => load());
  }, [load]);

  function resetForm() {
    setWeekday(0);
    setStartTime("09:00");
    setEndTime("10:00");
    setRoom("");
    setCourseId(courses[0]?.id || "");
    setEditingId(null);
  }

  function beginEdit(item: ScheduleTemplate) {
    setEditingId(item.id);
    setWeekday(item.weekday);
    setStartTime(item.start_time);
    setEndTime(item.end_time);
    setRoom(item.room);
    setCourseId(item.course_id || "");
  }

  async function save() {
    if (!courseId) {
      setError("Select a course first.");
      return;
    }

    const start = normalizeTime(startTime);
    const end = normalizeTime(endTime);

    if (!start || !end) {
      setError("Use 24-hour time in HH:MM format.");
      return;
    }

    if (end <= start) {
      setError("End time must be after start time.");
      return;
    }

    if (!room.trim()) {
      setError("Room is required.");
      return;
    }

    try {
      setWorking(true);
      setError("");

      if (editingId) {
        await updateScheduleTemplate(editingId, {
          weekday,
          start_time: start,
          end_time: end,
          room: room.trim(),
          course_id: courseId,
        });
      } else {
        await createScheduleTemplate({
          weekday,
          start_time: start,
          end_time: end,
          room: room.trim(),
          item_type: "class",
          course_id: courseId,
        });
      }

      resetForm();
      await load();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't save timetable entry."
      );
    } finally {
      setWorking(false);
    }
  }

  function confirmDelete(item: ScheduleTemplate) {
    Alert.alert(
      "Delete timetable entry?",
      `${item.subject} on ${WEEKDAYS[item.weekday]} at ${item.start_time}`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () =>
            void (async () => {
              try {
                setWorking(true);
                setError("");
                await deleteScheduleTemplate(item.id);
                if (editingId === item.id) {
                  resetForm();
                }
                await load();
              } catch (err) {
                setError(
                  err instanceof Error
                    ? err.message
                    : "Couldn't delete timetable entry."
                );
              } finally {
                setWorking(false);
              }
            })(),
        },
      ]
    );
  }

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6FC5FF" />
          <Text style={styles.stateText}>Loading timetable...</Text>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.topBar}>
          <Pressable onPress={() => router.back()} style={styles.backButton}>
            <Text style={styles.back}>‹</Text>
          </Pressable>

          <View style={styles.topBarText}>
            <Text style={styles.eyebrow}>ACADEMIC SETUP</Text>
            <Text style={styles.title}>Timetable</Text>
            <Text style={styles.subtitle}>
              Build the recurring weekly teaching schedule.
            </Text>
          </View>
        </View>

        {error ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        {courses.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>Create a course first</Text>
            <Text style={styles.emptyText}>
              Timetable classes are linked to your courses, so start by creating
              one in Course Workspace.
            </Text>

            <Pressable
              style={styles.primaryButton}
              onPress={() => router.push("/courses/new")}
            >
              <Text style={styles.primaryText}>Create Course</Text>
            </Pressable>
          </View>
        ) : (
          <>
            <View style={styles.editorCard}>
              <View style={styles.editorHeader}>
                <View>
                  <Text style={styles.sectionLabel}>
                    {editingId ? "EDIT CLASS" : "NEW CLASS"}
                  </Text>
                  <Text style={styles.editorTitle}>
                    {editingId
                      ? "Update recurring class"
                      : "Add recurring class"}
                  </Text>
                </View>

                {editingId ? (
                  <Pressable onPress={resetForm} disabled={working}>
                    <Text style={styles.cancelEdit}>Cancel edit</Text>
                  </Pressable>
                ) : null}
              </View>

              <Text style={styles.label}>Course</Text>

              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.courseRow}
              >
                {courses.map((course) => (
                  <Pressable
                    key={course.id}
                    style={[
                      styles.courseChip,
                      courseId === course.id && styles.courseChipActive,
                    ]}
                    onPress={() => setCourseId(course.id)}
                    disabled={working}
                  >
                    <Text
                      style={[
                        styles.courseChipCode,
                        courseId === course.id &&
                          styles.courseChipCodeActive,
                      ]}
                    >
                      {course.short_name || course.code}
                    </Text>
                    <Text
                      style={[
                        styles.courseChipSection,
                        courseId === course.id &&
                          styles.courseChipSectionActive,
                      ]}
                    >
                      {course.section}
                    </Text>
                  </Pressable>
                ))}
              </ScrollView>

              <Text style={styles.label}>Day</Text>

              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.dayRow}
              >
                {WEEKDAYS.map((day, index) => (
                  <Pressable
                    key={day}
                    style={[
                      styles.dayChip,
                      weekday === index && styles.dayChipActive,
                    ]}
                    onPress={() => setWeekday(index)}
                    disabled={working}
                  >
                    <Text
                      style={[
                        styles.dayText,
                        weekday === index && styles.dayTextActive,
                      ]}
                    >
                      {day.slice(0, 3)}
                    </Text>
                  </Pressable>
                ))}
              </ScrollView>

              <View style={styles.timeRow}>
                <View style={styles.timeField}>
                  <Text style={styles.label}>Start</Text>
                  <TextInput
                    style={styles.input}
                    value={startTime}
                    onChangeText={setStartTime}
                    placeholder="09:00"
                    placeholderTextColor="#68727F"
                    keyboardType="numbers-and-punctuation"
                    editable={!working}
                  />
                </View>

                <View style={styles.timeField}>
                  <Text style={styles.label}>End</Text>
                  <TextInput
                    style={styles.input}
                    value={endTime}
                    onChangeText={setEndTime}
                    placeholder="10:00"
                    placeholderTextColor="#68727F"
                    keyboardType="numbers-and-punctuation"
                    editable={!working}
                  />
                </View>
              </View>

              <Text style={styles.label}>Room</Text>
              <TextInput
                style={styles.input}
                value={room}
                onChangeText={setRoom}
                placeholder="LT-1"
                placeholderTextColor="#68727F"
                editable={!working}
              />

              <Pressable
                style={[
                  styles.primaryButton,
                  working && styles.disabledButton,
                ]}
                onPress={() => void save()}
                disabled={working}
              >
                <Text style={styles.primaryText}>
                  {working
                    ? "Saving..."
                    : editingId
                      ? "Save Changes"
                      : "Add to Timetable"}
                </Text>
              </Pressable>
            </View>

            <Text style={styles.sectionTitle}>
              Recurring classes
            </Text>

            {templates.length === 0 ? (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyTitle}>
                  Your timetable is empty
                </Text>
                <Text style={styles.emptyText}>
                  Add your first recurring class above. ProfPilot will reject
                  overlapping slots automatically.
                </Text>
              </View>
            ) : (
              templates.map((item) => (
                <View key={item.id} style={styles.classCard}>
                  <View style={styles.classTime}>
                    <Text style={styles.classDay}>
                      {WEEKDAYS[item.weekday]}
                    </Text>
                    <Text style={styles.classTimeText}>
                      {item.start_time}–{item.end_time}
                    </Text>
                  </View>

                  <View style={styles.classMain}>
                    <Text style={styles.classSubject}>
                      {item.subject}
                    </Text>
                    <Text style={styles.classMeta}>
                      {item.code
                        ? `${item.code} · ${item.batch}`
                        : item.batch}
                    </Text>
                    <Text style={styles.classRoom}>
                      {item.room || "Room not assigned"}
                    </Text>
                  </View>

                  <View style={styles.classActions}>
                    <Pressable
                      style={styles.iconButton}
                      onPress={() => beginEdit(item)}
                      disabled={working}
                    >
                      <Text style={styles.iconText}>✎</Text>
                    </Pressable>

                    <Pressable
                      style={styles.iconButton}
                      onPress={() => confirmDelete(item)}
                      disabled={working}
                    >
                      <Text style={styles.deleteText}>⌫</Text>
                    </Pressable>
                  </View>
                </View>
              ))
            )}
          </>
        )}

        <View style={{ height: 35 }} />
      </ScrollView>
    </KeyboardAvoidingView>
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
    paddingBottom: 40,
  },

  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },

  stateText: {
    color: "#7E8794",
    marginTop: 12,
  },

  topBar: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 24,
  },

  backButton: {
    marginRight: 10,
    paddingRight: 8,
  },

  back: {
    color: "#FFFFFF",
    fontSize: 38,
    lineHeight: 38,
  },

  topBarText: {
    flex: 1,
  },

  eyebrow: {
    color: "#6FC5FF",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 1.1,
  },

  title: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "800",
    marginTop: 3,
  },

  subtitle: {
    color: "#76818D",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },

  errorBanner: {
    backgroundColor: "#2A1B1E",
    borderWidth: 1,
    borderColor: "#513036",
    borderRadius: 12,
    padding: 12,
    marginBottom: 14,
  },

  errorText: {
    color: "#FFB0B0",
    fontSize: 11,
    lineHeight: 17,
  },

  editorCard: {
    backgroundColor: "#171A20",
    borderRadius: 19,
    padding: 17,
    marginBottom: 23,
  },

  editorHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 15,
  },

  sectionLabel: {
    color: "#6FC5FF",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 1,
  },

  editorTitle: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
    marginTop: 4,
  },

  cancelEdit: {
    color: "#7D8995",
    fontSize: 10,
    fontWeight: "600",
  },

  label: {
    color: "#AAB3BE",
    fontSize: 11,
    fontWeight: "600",
    marginBottom: 7,
  },

  courseRow: {
    gap: 8,
    paddingBottom: 16,
  },

  courseChip: {
    minWidth: 82,
    backgroundColor: "#0F1216",
    borderWidth: 1,
    borderColor: "#292F37",
    borderRadius: 11,
    paddingHorizontal: 11,
    paddingVertical: 9,
  },

  courseChipActive: {
    backgroundColor: "#23303A",
    borderColor: "#6FC5FF",
  },

  courseChipCode: {
    color: "#DDE3E8",
    fontSize: 11,
    fontWeight: "800",
  },

  courseChipCodeActive: {
    color: "#FFFFFF",
  },

  courseChipSection: {
    color: "#68747F",
    fontSize: 9,
    marginTop: 3,
  },

  courseChipSectionActive: {
    color: "#9ECFEF",
  },

  dayRow: {
    gap: 7,
    paddingBottom: 17,
  },

  dayChip: {
    borderRadius: 10,
    backgroundColor: "#0F1216",
    borderWidth: 1,
    borderColor: "#292F37",
    paddingHorizontal: 12,
    paddingVertical: 9,
  },

  dayChipActive: {
    backgroundColor: "#23303A",
    borderColor: "#6FC5FF",
  },

  dayText: {
    color: "#7B8793",
    fontSize: 10,
    fontWeight: "700",
  },

  dayTextActive: {
    color: "#FFFFFF",
  },

  timeRow: {
    flexDirection: "row",
    gap: 9,
  },

  timeField: {
    flex: 1,
  },

  input: {
    height: 48,
    backgroundColor: "#0F1216",
    borderWidth: 1,
    borderColor: "#292F37",
    borderRadius: 12,
    paddingHorizontal: 13,
    color: "#FFFFFF",
    fontSize: 12,
    marginBottom: 15,
  },

  primaryButton: {
    minHeight: 50,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 3,
  },

  disabledButton: {
    opacity: 0.55,
  },

  primaryText: {
    color: "#0B0D10",
    fontSize: 12,
    fontWeight: "800",
  },

  emptyCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 22,
    alignItems: "center",
    marginBottom: 13,
  },

  emptyTitle: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
    textAlign: "center",
  },

  emptyText: {
    color: "#7F8B97",
    fontSize: 11,
    lineHeight: 17,
    textAlign: "center",
    marginTop: 7,
  },

  sectionTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 12,
  },

  classCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 16,
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
  },

  classTime: {
    width: 91,
  },

  classDay: {
    color: "#6FC5FF",
    fontSize: 10,
    fontWeight: "800",
  },

  classTimeText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
    marginTop: 5,
  },

  classMain: {
    flex: 1,
    paddingHorizontal: 8,
  },

  classSubject: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
  },

  classMeta: {
    color: "#7E8995",
    fontSize: 10,
    marginTop: 4,
  },

  classRoom: {
    color: "#626E7A",
    fontSize: 9,
    marginTop: 5,
  },

  classActions: {
    flexDirection: "row",
    gap: 5,
  },

  iconButton: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: "#252C34",
    alignItems: "center",
    justifyContent: "center",
  },

  iconText: {
    color: "#CDD4DB",
    fontSize: 11,
    fontWeight: "700",
  },

  deleteText: {
    color: "#FF9B9B",
    fontSize: 11,
    fontWeight: "700",
  },
});
