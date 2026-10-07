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
import { useLocalSearchParams, useRouter } from "expo-router";

import {
  CourseDetail,
  SyllabusUnit,
  SyllabusTopic,
  createSyllabusUnit,
  createSyllabusTopic,
  deleteSyllabusTopic,
  deleteSyllabusUnit,
  getCourse,
  reorderSyllabusTopics,
  reorderSyllabusUnits,
  updateSyllabusTopic,
  updateSyllabusUnit,
} from "../../../services/api";

export default function SyllabusEditorScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const courseId = Array.isArray(id) ? id[0] : id;

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");

  const [newUnitName, setNewUnitName] = useState("");
  const [newTopicName, setNewTopicName] = useState<Record<string, string>>({});
  const [newTopicDate, setNewTopicDate] = useState<Record<string, string>>({});

  const [editingUnitId, setEditingUnitId] = useState<string | null>(null);
  const [editingUnitName, setEditingUnitName] = useState("");

  const [editingTopicId, setEditingTopicId] = useState<string | null>(null);
  const [editingTopicName, setEditingTopicName] = useState("");
  const [editingTopicDate, setEditingTopicDate] = useState("");
  const [editingTopicUnitId, setEditingTopicUnitId] = useState<string | null>(null);

  const loadCourse = useCallback(async () => {
    if (!courseId) {
      setError("Course id is missing.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError("");
      const data = await getCourse(courseId);
      setCourse(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't load syllabus."
      );
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    void Promise.resolve().then(() => loadCourse());
  }, [loadCourse]);

  async function runMutation(operation: () => Promise<unknown>) {
    try {
      setWorking(true);
      setError("");
      await operation();
      await loadCourse();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't update syllabus."
      );
    } finally {
      setWorking(false);
    }
  }

  async function addUnit() {
    const name = newUnitName.trim();
    if (!name || !courseId) return;

    await runMutation(async () => {
      await createSyllabusUnit(courseId, { name });
      setNewUnitName("");
    });
  }

  function beginUnitEdit(unit: SyllabusUnit) {
    setEditingUnitId(unit.id);
    setEditingUnitName(unit.name);
  }

  async function saveUnitEdit() {
    const name = editingUnitName.trim();
    if (!courseId || !editingUnitId || !name) return;

    const unitId = editingUnitId;

    await runMutation(async () => {
      await updateSyllabusUnit(courseId, unitId, name);
      setEditingUnitId(null);
      setEditingUnitName("");
    });
  }

  function confirmDeleteUnit(unit: SyllabusUnit) {
    if (!courseId) return;

    Alert.alert(
      "Delete unit?",
      `“${unit.name}” and all its topics will be removed.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () =>
            void runMutation(() =>
              deleteSyllabusUnit(courseId, unit.id)
            ),
        },
      ]
    );
  }

  async function moveUnit(unitIndex: number, direction: -1 | 1) {
    if (!courseId || !course) return;

    const target = unitIndex + direction;
    if (target < 0 || target >= course.syllabus.length) return;

    const ids = course.syllabus.map((unit) => unit.id);
    [ids[unitIndex], ids[target]] = [ids[target], ids[unitIndex]];

    await runMutation(async () => {
      await reorderSyllabusUnits(courseId, ids);
    });
  }

  async function addTopic(unitId: string) {
    if (!courseId) return;

    const name = (newTopicName[unitId] || "").trim();
    const plannedDate = (newTopicDate[unitId] || "").trim();

    if (!name) return;

    await runMutation(async () => {
      await createSyllabusTopic(courseId, unitId, {
        name,
        planned_date: plannedDate || null,
      });

      setNewTopicName((previous) => ({
        ...previous,
        [unitId]: "",
      }));

      setNewTopicDate((previous) => ({
        ...previous,
        [unitId]: "",
      }));
    });
  }

  function beginTopicEdit(unitId: string, topic: SyllabusTopic) {
    setEditingTopicId(topic.id);
    setEditingTopicUnitId(unitId);
    setEditingTopicName(topic.name);
    setEditingTopicDate(topic.planned_date || "");
  }

  async function saveTopicEdit() {
    if (
      !courseId ||
      !editingTopicId ||
      !editingTopicUnitId ||
      !editingTopicName.trim()
    ) {
      return;
    }

    const topicId = editingTopicId;
    const unitId = editingTopicUnitId;
    const plannedDate = editingTopicDate.trim();

    await runMutation(async () => {
      await updateSyllabusTopic(courseId, unitId, topicId, {
        name: editingTopicName.trim(),
        planned_date: plannedDate || undefined,
        clear_planned_date: !plannedDate,
      });

      setEditingTopicId(null);
      setEditingTopicUnitId(null);
      setEditingTopicName("");
      setEditingTopicDate("");
    });
  }

  function confirmDeleteTopic(unitId: string, topic: SyllabusTopic) {
    if (!courseId) return;

    Alert.alert(
      "Delete topic?",
      `Remove “${topic.name}” from this unit?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () =>
            void runMutation(() =>
              deleteSyllabusTopic(courseId, unitId, topic.id)
            ),
        },
      ]
    );
  }

  async function moveTopic(
    unit: SyllabusUnit,
    topicIndex: number,
    direction: -1 | 1
  ) {
    if (!courseId) return;

    const target = topicIndex + direction;
    if (target < 0 || target >= unit.topics.length) return;

    const ids = unit.topics.map((topic) => topic.id);
    [ids[topicIndex], ids[target]] = [ids[target], ids[topicIndex]];

    await runMutation(async () => {
      await reorderSyllabusTopics(courseId, unit.id, ids);
    });
  }

  if (loading) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6FC5FF" />
          <Text style={styles.stateText}>Loading syllabus...</Text>
        </View>
      </View>
    );
  }

  if (!course) {
    return (
      <View style={styles.screen}>
        <View style={styles.center}>
          <Text style={styles.errorTitle}>Syllabus unavailable</Text>
          <Text style={styles.errorText}>{error || "Course not found."}</Text>
          <Pressable style={styles.primaryButton} onPress={() => void loadCourse()}>
            <Text style={styles.primaryText}>Retry</Text>
          </Pressable>
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
            <Text style={styles.eyebrow}>COURSE WORKSPACE</Text>
            <Text style={styles.title}>Syllabus</Text>
            <Text style={styles.subtitle}>
              {course.code} · {course.section}
            </Text>
          </View>
        </View>

        {error ? (
          <View style={styles.errorBanner}>
            <Text style={styles.errorBannerText}>{error}</Text>
          </View>
        ) : null}

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>Build the teaching plan</Text>
          <Text style={styles.infoText}>
            Add units and topics here. Topic completion is recorded through
            lecture coverage, while planned dates drive ProfPilot&apos;s pacing and
            completion intelligence.
          </Text>
        </View>

        <View style={styles.addUnitCard}>
          <Text style={styles.sectionLabel}>NEW UNIT</Text>

          <View style={styles.inlineRow}>
            <TextInput
              style={styles.inlineInput}
              placeholder="e.g. Unit 1 · Process Management"
              placeholderTextColor="#68727F"
              value={newUnitName}
              onChangeText={setNewUnitName}
              editable={!working}
            />

            <Pressable
              style={styles.smallPrimary}
              onPress={() => void addUnit()}
              disabled={working || !newUnitName.trim()}
            >
              <Text style={styles.smallPrimaryText}>Add</Text>
            </Pressable>
          </View>
        </View>

        {course.syllabus.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>No syllabus yet</Text>
            <Text style={styles.emptyText}>
              Start with a unit, then add the topics you plan to teach.
            </Text>
          </View>
        ) : (
          course.syllabus.map((unit, unitIndex) => (
            <View key={unit.id} style={styles.unitCard}>
              <View style={styles.unitHeader}>
                <View style={styles.unitHeaderMain}>
                  {editingUnitId === unit.id ? (
                    <View style={styles.editRow}>
                      <TextInput
                        style={styles.editInput}
                        value={editingUnitName}
                        onChangeText={setEditingUnitName}
                        autoFocus
                        editable={!working}
                      />
                      <Pressable
                        style={styles.iconButton}
                        onPress={() => void saveUnitEdit()}
                        disabled={working || !editingUnitName.trim()}
                      >
                        <Text style={styles.iconText}>✓</Text>
                      </Pressable>
                      <Pressable
                        style={styles.iconButton}
                        onPress={() => {
                          setEditingUnitId(null);
                          setEditingUnitName("");
                        }}
                        disabled={working}
                      >
                        <Text style={styles.iconText}>×</Text>
                      </Pressable>
                    </View>
                  ) : (
                    <>
                      <Text style={styles.unitName}>{unit.name}</Text>
                      <Text style={styles.unitMeta}>
                        {unit.topics.length} topic
                        {unit.topics.length === 1 ? "" : "s"} ·{" "}
                        {Math.round(unit.progress)}% covered
                      </Text>
                    </>
                  )}
                </View>

                {editingUnitId !== unit.id ? (
                  <View style={styles.actionRow}>
                    <Pressable
                      style={styles.iconButton}
                      onPress={() => void moveUnit(unitIndex, -1)}
                      disabled={working || unitIndex === 0}
                    >
                      <Text
                        style={[
                          styles.iconText,
                          unitIndex === 0 && styles.disabledIcon,
                        ]}
                      >
                        ↑
                      </Text>
                    </Pressable>

                    <Pressable
                      style={styles.iconButton}
                      onPress={() => void moveUnit(unitIndex, 1)}
                      disabled={
                        working ||
                        unitIndex === course.syllabus.length - 1
                      }
                    >
                      <Text
                        style={[
                          styles.iconText,
                          unitIndex === course.syllabus.length - 1 &&
                            styles.disabledIcon,
                        ]}
                      >
                        ↓
                      </Text>
                    </Pressable>

                    <Pressable
                      style={styles.iconButton}
                      onPress={() => beginUnitEdit(unit)}
                      disabled={working}
                    >
                      <Text style={styles.iconText}>✎</Text>
                    </Pressable>

                    <Pressable
                      style={styles.iconButton}
                      onPress={() => confirmDeleteUnit(unit)}
                      disabled={working}
                    >
                      <Text style={styles.deleteIcon}>⌫</Text>
                    </Pressable>
                  </View>
                ) : null}
              </View>

              <View style={styles.progressTrack}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${Math.min(
                        100,
                        Math.max(0, unit.progress)
                      )}%`,
                    },
                  ]}
                />
              </View>

              {unit.topics.map((topic, topicIndex) => (
                <View key={topic.id} style={styles.topicRow}>
                  {editingTopicId === topic.id ? (
                    <View style={styles.topicEditor}>
                      <TextInput
                        style={styles.editInput}
                        value={editingTopicName}
                        onChangeText={setEditingTopicName}
                        autoFocus
                        editable={!working}
                      />

                      <TextInput
                        style={styles.editInput}
                        placeholder="Planned date · YYYY-MM-DD"
                        placeholderTextColor="#68727F"
                        value={editingTopicDate}
                        onChangeText={setEditingTopicDate}
                        editable={!working}
                        autoCapitalize="none"
                      />

                      <View style={styles.actionRow}>
                        <Pressable
                          style={styles.smallPrimary}
                          onPress={() => void saveTopicEdit()}
                          disabled={working || !editingTopicName.trim()}
                        >
                          <Text style={styles.smallPrimaryText}>Save</Text>
                        </Pressable>

                        <Pressable
                          style={styles.smallSecondary}
                          onPress={() => {
                            setEditingTopicId(null);
                            setEditingTopicUnitId(null);
                            setEditingTopicName("");
                            setEditingTopicDate("");
                          }}
                          disabled={working}
                        >
                          <Text style={styles.smallSecondaryText}>Cancel</Text>
                        </Pressable>
                      </View>
                    </View>
                  ) : (
                    <>
                      <View style={styles.topicMain}>
                        <Text
                          style={[
                            styles.topicStatus,
                            topic.completed && styles.topicDone,
                          ]}
                        >
                          {topic.completed ? "✓" : "○"}
                        </Text>

                        <View style={styles.topicTextBox}>
                          <Text
                            style={[
                              styles.topicName,
                              topic.completed && styles.topicCompleted,
                            ]}
                          >
                            {topic.name}
                          </Text>

                          {topic.planned_date ? (
                            <Text style={styles.topicDate}>
                              Planned {topic.planned_date}
                            </Text>
                          ) : null}
                        </View>
                      </View>

                      <View style={styles.topicActions}>
                        <Pressable
                          style={styles.tinyButton}
                          onPress={() => void moveTopic(unit, topicIndex, -1)}
                          disabled={working || topicIndex === 0}
                        >
                          <Text
                            style={[
                              styles.tinyText,
                              topicIndex === 0 && styles.disabledIcon,
                            ]}
                          >
                            ↑
                          </Text>
                        </Pressable>

                        <Pressable
                          style={styles.tinyButton}
                          onPress={() => void moveTopic(unit, topicIndex, 1)}
                          disabled={
                            working ||
                            topicIndex === unit.topics.length - 1
                          }
                        >
                          <Text
                            style={[
                              styles.tinyText,
                              topicIndex === unit.topics.length - 1 &&
                                styles.disabledIcon,
                            ]}
                          >
                            ↓
                          </Text>
                        </Pressable>

                        <Pressable
                          style={styles.tinyButton}
                          onPress={() =>
                            beginTopicEdit(unit.id, topic)
                          }
                          disabled={working}
                        >
                          <Text style={styles.tinyText}>✎</Text>
                        </Pressable>

                        <Pressable
                          style={styles.tinyButton}
                          onPress={() =>
                            confirmDeleteTopic(unit.id, topic)
                          }
                          disabled={working}
                        >
                          <Text style={styles.deleteIcon}>⌫</Text>
                        </Pressable>
                      </View>
                    </>
                  )}
                </View>
              ))}

              <View style={styles.addTopicBox}>
                <Text style={styles.addTopicLabel}>ADD TOPIC</Text>

                <TextInput
                  style={styles.topicInput}
                  placeholder="e.g. Context switching"
                  placeholderTextColor="#68727F"
                  value={newTopicName[unit.id] || ""}
                  onChangeText={(value) =>
                    setNewTopicName((previous) => ({
                      ...previous,
                      [unit.id]: value,
                    }))
                  }
                  editable={!working}
                />

                <View style={styles.inlineRow}>
                  <TextInput
                    style={styles.topicDateInput}
                    placeholder="Planned date · YYYY-MM-DD"
                    placeholderTextColor="#68727F"
                    value={newTopicDate[unit.id] || ""}
                    onChangeText={(value) =>
                      setNewTopicDate((previous) => ({
                        ...previous,
                        [unit.id]: value,
                      }))
                    }
                    editable={!working}
                    autoCapitalize="none"
                  />

                  <Pressable
                    style={styles.smallPrimary}
                    onPress={() => void addTopic(unit.id)}
                    disabled={
                      working ||
                      !(newTopicName[unit.id] || "").trim()
                    }
                  >
                    <Text style={styles.smallPrimaryText}>Add topic</Text>
                  </Pressable>
                </View>
              </View>
            </View>
          ))
        )}

        <View style={{ height: 45 }} />
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
    padding: 25,
  },

  stateText: {
    color: "#7E8794",
    marginTop: 12,
  },

  topBar: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 22,
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
    marginTop: 3,
  },

  infoCard: {
    backgroundColor: "#121820",
    borderRadius: 18,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#1E2A35",
  },

  infoTitle: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },

  infoText: {
    color: "#7F8B97",
    fontSize: 11,
    lineHeight: 17,
    marginTop: 6,
  },

  addUnitCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 16,
    marginBottom: 14,
  },

  sectionLabel: {
    color: "#6FC5FF",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 1,
    marginBottom: 9,
  },

  inlineRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },

  inlineInput: {
    flex: 1,
    height: 48,
    backgroundColor: "#0F1216",
    borderWidth: 1,
    borderColor: "#272D35",
    borderRadius: 12,
    paddingHorizontal: 13,
    color: "#FFFFFF",
    fontSize: 12,
  },

  smallPrimary: {
    backgroundColor: "#FFFFFF",
    borderRadius: 10,
    minHeight: 40,
    paddingHorizontal: 13,
    alignItems: "center",
    justifyContent: "center",
  },

  smallPrimaryText: {
    color: "#0B0D10",
    fontSize: 11,
    fontWeight: "800",
  },

  smallSecondary: {
    backgroundColor: "#242B33",
    borderRadius: 10,
    minHeight: 40,
    paddingHorizontal: 13,
    alignItems: "center",
    justifyContent: "center",
  },

  smallSecondaryText: {
    color: "#E2E7EC",
    fontSize: 11,
    fontWeight: "700",
  },

  emptyCard: {
    backgroundColor: "#171A20",
    borderRadius: 18,
    padding: 22,
    alignItems: "center",
  },

  emptyTitle: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },

  emptyText: {
    color: "#7F8B97",
    fontSize: 12,
    lineHeight: 18,
    textAlign: "center",
    marginTop: 7,
  },

  unitCard: {
    backgroundColor: "#171A20",
    borderRadius: 19,
    padding: 16,
    marginBottom: 13,
  },

  unitHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
  },

  unitHeaderMain: {
    flex: 1,
    paddingRight: 8,
  },

  unitName: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },

  unitMeta: {
    color: "#707B87",
    fontSize: 10,
    marginTop: 4,
  },

  actionRow: {
    flexDirection: "row",
    alignItems: "center",
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
    fontSize: 12,
    fontWeight: "700",
  },

  deleteIcon: {
    color: "#FF9B9B",
    fontSize: 12,
    fontWeight: "700",
  },

  disabledIcon: {
    opacity: 0.25,
  },

  editRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },

  editInput: {
    flex: 1,
    minHeight: 42,
    backgroundColor: "#0F1216",
    borderWidth: 1,
    borderColor: "#303741",
    borderRadius: 10,
    paddingHorizontal: 11,
    color: "#FFFFFF",
    fontSize: 12,
  },

  progressTrack: {
    height: 5,
    backgroundColor: "#292E36",
    borderRadius: 3,
    marginTop: 11,
    marginBottom: 5,
    overflow: "hidden",
  },

  progressFill: {
    height: "100%",
    backgroundColor: "#6FC5FF",
    borderRadius: 3,
  },

  topicRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: "#232931",
  },

  topicMain: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    paddingRight: 7,
  },

  topicStatus: {
    color: "#66717D",
    width: 22,
    fontSize: 13,
  },

  topicDone: {
    color: "#72D6A0",
  },

  topicTextBox: {
    flex: 1,
  },

  topicName: {
    color: "#DDE2E7",
    fontSize: 12,
    lineHeight: 17,
  },

  topicCompleted: {
    color: "#7F8A96",
  },

  topicDate: {
    color: "#65717D",
    fontSize: 9,
    marginTop: 3,
  },

  topicActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },

  tinyButton: {
    width: 25,
    height: 25,
    borderRadius: 7,
    backgroundColor: "#222931",
    alignItems: "center",
    justifyContent: "center",
  },

  tinyText: {
    color: "#C6CED6",
    fontSize: 10,
    fontWeight: "700",
  },

  topicEditor: {
    flex: 1,
    gap: 7,
    paddingVertical: 4,
  },

  addTopicBox: {
    borderTopWidth: 1,
    borderTopColor: "#292F37",
    marginTop: 6,
    paddingTop: 13,
  },

  addTopicLabel: {
    color: "#66727E",
    fontSize: 8,
    fontWeight: "800",
    letterSpacing: 1,
    marginBottom: 7,
  },

  topicInput: {
    height: 43,
    backgroundColor: "#0F1216",
    borderWidth: 1,
    borderColor: "#282F38",
    borderRadius: 10,
    paddingHorizontal: 11,
    color: "#FFFFFF",
    fontSize: 11,
    marginBottom: 8,
  },

  topicDateInput: {
    flex: 1,
    height: 40,
    backgroundColor: "#0F1216",
    borderWidth: 1,
    borderColor: "#282F38",
    borderRadius: 10,
    paddingHorizontal: 11,
    color: "#FFFFFF",
    fontSize: 10,
  },

  errorBanner: {
    backgroundColor: "#2A1B1E",
    borderWidth: 1,
    borderColor: "#513036",
    borderRadius: 12,
    padding: 12,
    marginBottom: 13,
  },

  errorBannerText: {
    color: "#FFB0B0",
    fontSize: 11,
    lineHeight: 17,
  },

  errorTitle: {
    color: "#FFFFFF",
    fontSize: 20,
    fontWeight: "700",
  },

  errorText: {
    color: "#7E8794",
    textAlign: "center",
    lineHeight: 18,
    marginTop: 8,
  },

  primaryButton: {
    backgroundColor: "#FFFFFF",
    borderRadius: 11,
    paddingHorizontal: 17,
    paddingVertical: 10,
    marginTop: 18,
  },

  primaryText: {
    color: "#0B0D10",
    fontSize: 12,
    fontWeight: "800",
  },
});
