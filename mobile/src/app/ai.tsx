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

import { useRef, useState } from "react";
import { useRouter } from "expo-router";

import {
  queryProfPilotAI,
  AIQueryResponse,
} from "../services/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  response?: AIQueryResponse;
};

const suggestions = [
  "When will I finish my DBMS syllabus?",
  "What if I cancel my next DBMS class?",
  "What did I teach in my last DBMS lecture?",
  "Which students are below 75% attendance?",
];

export default function AIScreen() {
  const router = useRouter();

  const scrollRef = useRef<ScrollView>(null);

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);

  const sendMessage = async (textOverride?: string) => {
    const text = (textOverride ?? message).trim();

    if (!text || loading) {
      return;
    }

    const userMessage: Message = {
      id: `${Date.now()}-user`,
      role: "user",
      text,
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);

    setMessage("");
    setLoading(true);

    setTimeout(() => {
      scrollRef.current?.scrollToEnd({
        animated: true,
      });
    }, 100);

    try {
      const result = await queryProfPilotAI({
        message: text,
        course_id: "dbms",
      });

      const assistantMessage: Message = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        text: result.answer,
        response: result,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

      setTimeout(() => {
        scrollRef.current?.scrollToEnd({
          animated: true,
        });
      }, 100);
    } catch (error) {
      const errorMessage: Message = {
        id: `${Date.now()}-error`,
        role: "assistant",
        text:
          "I couldn't connect to the ProfPilot server. Please make sure the backend is running and your phone can reach your laptop.",
      };

      setMessages((previous) => [
        ...previous,
        errorMessage,
      ]);
    } finally {
      setLoading(false);
    }
  };

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
          <Text style={styles.back}>‹</Text>
        </Pressable>

        <View style={styles.headerText}>
          <Text style={styles.title}>
            ProfPilot AI
          </Text>

          <Text style={styles.subtitle}>
            Academic companion
          </Text>
        </View>

        <View style={styles.statusContainer}>
          <View style={styles.statusDot} />
        </View>
      </View>

      {/* CHAT */}
      <ScrollView
        ref={scrollRef}
        style={styles.chat}
        contentContainerStyle={styles.chatContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {messages.length === 0 && (
          <>
            <View style={styles.welcomeCard}>
              <View style={styles.aiIcon}>
                <Text style={styles.aiIconText}>
                  ✦
                </Text>
              </View>

              <Text style={styles.welcomeTitle}>
                Good evening, Dr. Sharma
              </Text>

              <Text style={styles.welcomeText}>
                I'm ProfPilot, your academic
                companion. I can help you understand
                your schedule, courses, syllabus
                progress and academic workload.
              </Text>
            </View>

            <Text style={styles.sectionLabel}>
              TRY ASKING
            </Text>

            {suggestions.map((question) => (
              <Pressable
                key={question}
                style={({ pressed }) => [
                  styles.suggestion,
                  pressed && styles.pressed,
                ]}
                onPress={() =>
                  sendMessage(question)
                }
              >
                <Text style={styles.suggestionText}>
                  {question}
                </Text>

                <Text style={styles.arrow}>
                  →
                </Text>
              </Pressable>
            ))}
          </>
        )}

        {messages.map((item) => {
          const isUser = item.role === "user";

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
                  styles.messageBubble,
                  isUser
                    ? styles.userBubble
                    : styles.assistantBubble,
                ]}
              >
                {!isUser && (
                  <Text style={styles.messageLabel}>
                    PROFPILOT
                  </Text>
                )}

                <Text
                  style={[
                    styles.messageText,
                    isUser
                      ? styles.userText
                      : styles.assistantText,
                  ]}
                >
                  {item.text}
                </Text>

                {!isUser &&
                  item.response?.confidence !==
                    undefined && (
                    <Text style={styles.confidence}>
                      Confidence{" "}
                      {Math.round(
                        item.response.confidence *
                          100
                      )}
                      %
                    </Text>
                  )}

                {!isUser &&
                  item.response
                    ?.requires_confirmation && (
                    <View
                      style={
                        styles.confirmationBox
                      }
                    >
                      <Text
                        style={
                          styles.confirmationText
                        }
                      >
                        This action requires your
                        confirmation before it can be
                        executed.
                      </Text>

                      <View
                        style={
                          styles.confirmButtons
                        }
                      >
                        <Pressable
                          style={
                            styles.confirmButton
                          }
                        >
                          <Text
                            style={
                              styles.confirmButtonText
                            }
                          >
                            Review
                          </Text>
                        </Pressable>
                      </View>
                    </View>
                  )}
              </View>
            </View>
          );
        })}

        {loading && (
          <View
            style={[
              styles.messageRow,
              styles.assistantRow,
            ]}
          >
            <View
              style={[
                styles.messageBubble,
                styles.assistantBubble,
              ]}
            >
              <Text style={styles.messageLabel}>
                PROFPILOT
              </Text>

              <View style={styles.loadingRow}>
                <ActivityIndicator
                  size="small"
                  color="#6FC5FF"
                />

                <Text style={styles.loadingText}>
                  Thinking...
                </Text>
              </View>
            </View>
          </View>
        )}

        <View style={{ height: 30 }} />
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
          style={({ pressed }) => [
            styles.sendButton,
            pressed && styles.pressed,
            (!message.trim() || loading) &&
              styles.disabledButton,
          ]}
          onPress={() => sendMessage()}
          disabled={!message.trim() || loading}
        >
          <Text style={styles.sendText}>
            ↑
          </Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#0B0D10",
  },

  header: {
    height: 110,
    paddingHorizontal: 20,
    paddingTop: 55,
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

  headerText: {
    justifyContent: "center",
  },

  title: {
    color: "#FFFFFF",
    fontSize: 19,
    fontWeight: "700",
  },

  subtitle: {
    color: "#747E8B",
    fontSize: 12,
    marginTop: 3,
  },

  statusContainer: {
    marginLeft: "auto",
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

  welcomeCard: {
    backgroundColor: "#121820",
    borderRadius: 22,
    padding: 22,
    marginBottom: 28,
    borderWidth: 1,
    borderColor: "#1E2A35",
  },

  aiIcon: {
    width: 46,
    height: 46,
    borderRadius: 14,
    backgroundColor: "#1D2B37",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 15,
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
    marginTop: 9,
  },

  sectionLabel: {
    color: "#66707D",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.2,
    marginBottom: 12,
  },

  suggestion: {
    backgroundColor: "#171A20",
    borderRadius: 15,
    padding: 16,
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
  },

  pressed: {
    opacity: 0.7,
    transform: [{ scale: 0.98 }],
  },

  suggestionText: {
    color: "#E0E5EB",
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },

  arrow: {
    color: "#6FC5FF",
    fontSize: 20,
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

  messageBubble: {
    maxWidth: "87%",
    borderRadius: 18,
    padding: 15,
  },

  userBubble: {
    backgroundColor: "#2A3946",
    borderBottomRightRadius: 5,
  },

  assistantBubble: {
    backgroundColor: "#171A20",
    borderBottomLeftRadius: 5,
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
    fontSize: 14,
    lineHeight: 21,
  },

  userText: {
    color: "#F0F4F8",
  },

  assistantText: {
    color: "#DCE2E8",
  },

  confidence: {
    color: "#62707D",
    fontSize: 9,
    marginTop: 10,
  },

  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
  },

  loadingText: {
    color: "#798591",
    fontSize: 12,
    marginLeft: 8,
  },

  confirmationBox: {
    marginTop: 13,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#292F36",
  },

  confirmationText: {
    color: "#7F8995",
    fontSize: 10,
    lineHeight: 16,
  },

  confirmButtons: {
    flexDirection: "row",
    marginTop: 10,
  },

  confirmButton: {
    backgroundColor: "#FFFFFF",
    borderRadius: 9,
    paddingVertical: 8,
    paddingHorizontal: 13,
  },

  confirmButtonText: {
    color: "#0B0D10",
    fontSize: 11,
    fontWeight: "700",
  },

  inputArea: {
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: "#20242B",
    flexDirection: "row",
    alignItems: "flex-end",
    backgroundColor: "#0B0D10",
  },

  input: {
    flex: 1,
    minHeight: 48,
    maxHeight: 120,
    backgroundColor: "#171A20",
    borderRadius: 16,
    color: "#FFFFFF",
    paddingHorizontal: 16,
    paddingVertical: 13,
    fontSize: 14,
  },

  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 8,
  },

  disabledButton: {
    opacity: 0.35,
  },

  sendText: {
    color: "#0B0D10",
    fontSize: 24,
    fontWeight: "700",
  },
});