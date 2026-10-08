
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useLocalSearchParams,
  useRouter,
} from "expo-router";

import {
  executeAIAction,
  getAcademicContext,
  getMe,
  queryProfPilotAI,
  AIQueryResponse,
  AcademicContext,
} from "../services/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  response?: AIQueryResponse;
};

export default function AIScreen() {
  const router = useRouter();

  const { course_id } =
    useLocalSearchParams<{
      course_id?: string;
    }>();

  const scrollRef =
    useRef<ScrollView>(null);

  const [context, setContext] =
    useState<AcademicContext | null>(
      null
    );

  const selectedCourseId =
    Array.isArray(course_id)
      ? course_id[0]
      : course_id;

  const [activeCourseId, setActiveCourseId] =
    useState<string | undefined>(
      selectedCourseId
    );

  const [message, setMessage] =
    useState("");

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [executingId, setExecutingId] =
    useState<string | null>(null);

  const loadContext = useCallback(async () => {
    try {
      const me = await getMe();

      const data =
        await getAcademicContext(
          me.lecturer_id,
          selectedCourseId
        );

      setContext(data);

      setActiveCourseId(
        selectedCourseId ||
          data.selected_course?.id
      );
    } catch (error) {
      console.error(
        "AI context error:",
        error
      );
    }
  }, [selectedCourseId]);

  useEffect(() => {
    void loadContext();
  }, [loadContext]);

  const courseName =
    context?.selected_course?.short_name ||
    context?.selected_course?.name ||
    null;

  async function sendMessage(
    override?: string
  ) {
    const text =
      (
        override ??
        message
      ).trim();

    if (!text || loading) {
      return;
    }

    const userMessage: Message = {
      id:
        `${Date.now()}-user`,
      role: "user",
      text,
    };

    setMessages(
      (previous) => [
        ...previous,
        userMessage,
      ]
    );

    setMessage("");
    setLoading(true);

    setTimeout(() => {
      scrollRef.current?.scrollToEnd({
        animated: true,
      });
    }, 80);

    try {
      const requestData: {
        message: string;
        course_id?: string;
      } = {
        message: text,
      };

      if (activeCourseId) {
        requestData.course_id =
          activeCourseId;
      }

      const result =
        await queryProfPilotAI(
          requestData
        );

      const assistantMessage: Message = {
        id:
          `${Date.now()}-assistant`,
        role: "assistant",
        text: result.answer,
        response: result,
      };

      setMessages(
        (previous) => [
          ...previous,
          assistantMessage,
        ]
      );

      setTimeout(() => {
        scrollRef.current?.scrollToEnd({
          animated: true,
        });
      }, 80);
    } catch (error) {
      console.error(error);

      setMessages(
        (previous) => [
          ...previous,
          {
            id:
              `${Date.now()}-error`,
            role: "assistant",
            text:
              error instanceof Error
                ? error.message
                : "Couldn&apos;t connect to ProfPilot AI.",
          },
        ]
      );
    } finally {
      setLoading(false);
    }
  }

  async function confirmAction(
    item: Message
  ) {
    const actionPlan =
      item.response?.data
        ?.action_plan;
    console.log(
      "ACTION PLAN BEFORE EXECUTE:",
      JSON.stringify(
        actionPlan,
        null,
        2
      )
    );
    if (!actionPlan) {
      return;
    }

    try {
      setExecutingId(item.id);

      const result =
        await executeAIAction({
          confirmed: true,
          action_plan:
            actionPlan,
        });

      setMessages(
        (previous) =>
          previous.map(
            (message) =>
              message.id ===
              item.id
                ? {
                    ...message,
                    text:
                      `${message.text}\n\n${result.answer}`,
                    response:
                      result,
                  }
                : message
          )
      );
    } catch (error) {
      console.error(error);

      setMessages(
        (previous) => [
          ...previous,
          {
            id:
              `${Date.now()}-execute-error`,
            role: "assistant",
            text:
              error instanceof Error
                ? error.message
                : "Action execution failed.",
          },
        ]
      );
    } finally {
      setExecutingId(null);
    }
  }

  const suggestions = [
    courseName
      ? `When will I complete the ${courseName} syllabus?`
      : "When will I complete my syllabus?",

    courseName
      ? `What did I cover in my last ${courseName} lecture?`
      : "What did I cover in my last lecture?",

    "Which students are below 75% attendance?",
  ];

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={
        Platform.OS === "ios"
          ? "padding"
          : undefined
      }
    >
      {/* HEADER */}

      <View style={styles.header}>
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <Text style={styles.back}>
            ‹
          </Text>
        </Pressable>

        <View
          style={
            styles.headerContent
          }
        >
          <Text style={styles.title}>
            ProfPilot AI
          </Text>

          <Text style={styles.subtitle}>
            {courseName || "Academic companion"}
          </Text>
        </View>

        <View
          style={styles.statusDot}
        />
      </View>

      {/* CHAT */}

      <ScrollView
        ref={scrollRef}
        style={styles.chat}
        contentContainerStyle={
          styles.chatContent
        }
        showsVerticalScrollIndicator={
          false
        }
        keyboardShouldPersistTaps="handled"
      >
        {messages.length === 0 && (
          <>
            <View style={styles.welcome}>
              <View style={styles.aiIcon}>
                <Text
                  style={
                    styles.aiIconText
                  }
                >
                  ✦
                </Text>
              </View>

              <Text
                style={styles.welcomeTitle}
              >
                ProfPilot AI
              </Text>

              <Text
                style={styles.welcomeText}
              >
                Ask about courses, syllabus,
                schedule, attendance or your
                academic workload.
              </Text>
            </View>

            <Text style={styles.tryLabel}>
              TRY ASKING
            </Text>

            {suggestions.map(
              (question) => (
                <Pressable
                  key={question}
                  style={styles.suggestion}
                  onPress={() =>
                    sendMessage(
                      question
                    )
                  }
                >
                  <Text
                    style={
                      styles.suggestionText
                    }
                  >
                    {question}
                  </Text>

                  <Text
                    style={styles.arrow}
                  >
                    →
                  </Text>
                </Pressable>
              )
            )}
          </>
        )}

        {messages.map(
          (item) => {
            const isUser =
              item.role ===
              "user";

            const requiresConfirmation =
              !isUser &&
              item.response
                ?.requires_confirmation;

            return (
              <View
                key={item.id}
                style={[
                  styles.messageRow,
                  isUser
                    ? styles.userRow
                    : styles.assistantRow,
                ]}
              >
                <View
                  style={[
                    styles.bubble,
                    isUser
                      ? styles.userBubble
                      : styles.assistantBubble,
                  ]}
                >
                  {!isUser && (
                    <Text
                      style={
                        styles.messageLabel
                      }
                    >
                      PROFPILOT
                    </Text>
                  )}

                  <Text
                    style={
                      styles.messageText
                    }
                  >
                    {item.text}
                  </Text>

                  {!isUser &&
                    item.response
                      ?.confidence !==
                      undefined && (
                      <Text
                        style={
                          styles.confidence
                        }
                      >
                        Confidence{" "}
                        {Math.round(
                          item.response
                            .confidence *
                            100
                        )}
                        %
                      </Text>
                    )}

                  {requiresConfirmation && (
                    <View
                      style={
                        styles.confirmation
                      }
                    >
                      <Text
                        style={
                          styles.confirmationText
                        }
                      >
                        This action requires
                        your confirmation.
                      </Text>

                      <Pressable
                        style={
                          styles.confirmButton
                        }
                        onPress={() =>
                          confirmAction(
                            item
                          )
                        }
                        disabled={
                          executingId ===
                          item.id
                        }
                      >
                        <Text
                          style={
                            styles.confirmText
                          }
                        >
                          {executingId ===
                          item.id
                            ? "Executing..."
                            : "Confirm & Execute"}
                        </Text>
                      </Pressable>
                    </View>
                  )}
                </View>
              </View>
            );
          }
        )}

        {loading && (
          <View
            style={[
              styles.messageRow,
              styles.assistantRow,
            ]}
          >
            <View
              style={[
                styles.bubble,
                styles.assistantBubble,
              ]}
            >
              <ActivityIndicator
                color="#6FC5FF"
              />

              <Text
                style={styles.thinking}
              >
                Thinking...
              </Text>
            </View>
          </View>
        )}

        <View
          style={{ height: 20 }}
        />
      </ScrollView>

      {/* INPUT */}

      <View style={styles.inputArea}>
        <TextInput
          style={styles.input}
          placeholder="Ask ProfPilot..."
          placeholderTextColor="#66707D"
          value={message}
          onChangeText={setMessage}
          multiline
          maxLength={500}
        />

        <Pressable
          style={[
            styles.send,
            (!message.trim() ||
              loading) &&
              styles.sendDisabled,
          ]}
          onPress={() =>
            sendMessage()
          }
          disabled={
            !message.trim() ||
            loading
          }
        >
          <Text style={styles.sendText}>
            ↑
          </Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles =
  StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: "#0B0D10",
    },

    header: {
      height: 105,
      paddingHorizontal: 20,
      paddingTop: 50,
      flexDirection: "row",
      alignItems: "center",
      borderBottomWidth: 1,
      borderBottomColor: "#20242B",
    },

    backButton: {
      paddingRight: 14,
    },

    back: {
      color: "#FFFFFF",
      fontSize: 38,
      lineHeight: 38,
    },

    headerContent: {
      flex: 1,
    },

    title: {
      color: "#FFFFFF",
      fontSize: 19,
      fontWeight: "700",
    },

    subtitle: {
      color: "#6FC5FF",
      fontSize: 11,
      marginTop: 3,
    },

    statusDot: {
      width: 9,
      height: 9,
      borderRadius: 5,
      backgroundColor: "#72D6A0",
    },

    chat: {
      flex: 1,
    },

    chatContent: {
      padding: 20,
    },

    welcome: {
      backgroundColor: "#121820",
      borderRadius: 21,
      padding: 20,
      marginBottom: 25,
      borderWidth: 1,
      borderColor: "#1E2A35",
    },

    aiIcon: {
      width: 45,
      height: 45,
      borderRadius: 14,
      backgroundColor: "#1D2B37",
      alignItems: "center",
      justifyContent: "center",
      marginBottom: 14,
    },

    aiIconText: {
      color: "#6FC5FF",
      fontSize: 23,
    },

    welcomeTitle: {
      color: "#FFFFFF",
      fontSize: 20,
      fontWeight: "700",
    },

    welcomeText: {
      color: "#8A95A3",
      fontSize: 13,
      lineHeight: 20,
      marginTop: 8,
    },

    tryLabel: {
      color: "#66707D",
      fontSize: 10,
      fontWeight: "700",
      letterSpacing: 1,
      marginBottom: 10,
    },

    suggestion: {
      backgroundColor: "#171A20",
      borderRadius: 15,
      padding: 16,
      marginBottom: 10,
      flexDirection: "row",
      alignItems: "center",
    },

    suggestionText: {
      flex: 1,
      color: "#E0E5EB",
      fontSize: 13,
      lineHeight: 19,
    },

    arrow: {
      color: "#6FC5FF",
      fontSize: 18,
      marginLeft: 10,
    },

    messageRow: {
      width: "100%",
      marginBottom: 12,
    },

    userRow: {
      alignItems: "flex-end",
    },

    assistantRow: {
      alignItems: "flex-start",
    },

    bubble: {
      maxWidth: "88%",
      borderRadius: 18,
      padding: 15,
    },

    userBubble: {
      backgroundColor: "#2A3946",
    },

    assistantBubble: {
      backgroundColor: "#171A20",
      borderWidth: 1,
      borderColor: "#242B33",
    },

    messageLabel: {
      color: "#6FC5FF",
      fontSize: 9,
      fontWeight: "800",
      letterSpacing: 1,
      marginBottom: 7,
    },

    messageText: {
      color: "#E2E7EC",
      fontSize: 14,
      lineHeight: 21,
    },

    confidence: {
      color: "#62707D",
      fontSize: 9,
      marginTop: 9,
    },

    confirmation: {
      borderTopWidth: 1,
      borderTopColor: "#292F36",
      marginTop: 12,
      paddingTop: 12,
    },

    confirmationText: {
      color: "#7F8995",
      fontSize: 10,
      lineHeight: 16,
    },

    confirmButton: {
      alignSelf: "flex-start",
      backgroundColor: "#FFFFFF",
      borderRadius: 9,
      paddingHorizontal: 13,
      paddingVertical: 9,
      marginTop: 10,
    },

    confirmText: {
      color: "#0B0D10",
      fontSize: 11,
      fontWeight: "700",
    },

    thinking: {
      color: "#7E8794",
      fontSize: 11,
      marginTop: 8,
    },

    inputArea: {
      padding: 12,
      flexDirection: "row",
      borderTopWidth: 1,
      borderTopColor: "#20242B",
      backgroundColor: "#0B0D10",
    },

    input: {
      flex: 1,
      minHeight: 48,
      maxHeight: 110,
      backgroundColor: "#171A20",
      borderRadius: 16,
      color: "#FFFFFF",
      paddingHorizontal: 15,
      paddingVertical: 12,
      fontSize: 14,
    },

    send: {
      width: 48,
      height: 48,
      borderRadius: 16,
      backgroundColor: "#FFFFFF",
      justifyContent: "center",
      alignItems: "center",
      marginLeft: 8,
    },

    sendDisabled: {
      opacity: 0.35,
    },

    sendText: {
      color: "#0B0D10",
      fontSize: 24,
      fontWeight: "700",
    },
  });