import BottomNav from "../components/BottomNav";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";

const posts = [
  {
    name: "Dr. Mehta",
    department: "Computer Science",
    text: "Does anyone have good material for teaching B+ Trees?",
    likes: 8,
    comments: 4,
  },
  {
    name: "Dr. Rao",
    department: "Information Technology",
    text: "Sharing my latest DBMS assignment with the faculty.",
    likes: 13,
    comments: 6,
  },
  {
    name: "Dr. Kapoor",
    department: "Computer Science",
    text: "Has anyone tried a better way of tracking syllabus progress?",
    likes: 21,
    comments: 9,
  },
];

export default function CommunityScreen() {
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

        {/* Header */}
        <Text style={styles.title}>Faculty Community</Text>

        <Text style={styles.subtitle}>
          Connect, share and collaborate
        </Text>

        {/* Search */}
        <Pressable style={styles.search}>
          <Text style={styles.searchIcon}>⌕</Text>

          <Text style={styles.searchText}>
            Search faculty, posts & resources
          </Text>
        </Pressable>

        {/* AI Discovery Card */}
        <Pressable style={styles.aiCard}>
          <View style={styles.aiIcon}>
            <Text style={styles.aiIconText}>✦</Text>
          </View>

          <View style={styles.aiContent}>
            <Text style={styles.aiTitle}>
              Ask ProfPilot to find something
            </Text>

            <Text style={styles.aiSubtitle}>
              Find faculty, resources and discussions using natural language.
            </Text>
          </View>

          <Text style={styles.aiArrow}>›</Text>
        </Pressable>

        {/* Feed */}
        <View style={styles.feedHeader}>
          <Text style={styles.feedTitle}>Recent Discussions</Text>

          <Text style={styles.feedFilter}>Latest ▾</Text>
        </View>

        {posts.map((post, index) => (
          <Pressable
            style={({ pressed }) => [
              styles.post,
              pressed && styles.pressed,
            ]}
            key={index}
          >
            {/* Post Header */}
            <View style={styles.postHeader}>
              <View style={styles.smallAvatar}>
                <Text style={styles.avatarText}>
                  {post.name
                    .split(" ")
                    .map((x) => x[0])
                    .join("")}
                </Text>
              </View>

              <View style={styles.authorInfo}>
                <Text style={styles.postName}>
                  {post.name}
                </Text>

                <Text style={styles.department}>
                  {post.department}
                </Text>
              </View>

              <Text style={styles.more}>•••</Text>
            </View>

            {/* Post Content */}
            <Text style={styles.postText}>
              {post.text}
            </Text>

            {/* Stats */}
            <View style={styles.postFooter}>
              <Text style={styles.postStats}>
                ♡ {post.likes}
              </Text>

              <Text style={styles.postStats}>
                💬 {post.comments}
              </Text>

              <Text style={styles.reply}>
                View discussion →
              </Text>
            </View>
          </Pressable>
        ))}

        <View style={{ height: 30 }} />
      </ScrollView>

      <BottomNav />
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
    marginBottom: 22,
  },

  search: {
    height: 52,
    backgroundColor: "#171A20",
    borderRadius: 15,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 14,
  },

  searchIcon: {
    color: "#6D7885",
    fontSize: 23,
    marginRight: 10,
  },

  searchText: {
    color: "#67717D",
    fontSize: 13,
  },

  aiCard: {
    backgroundColor: "#121820",
    borderRadius: 18,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 28,
    borderWidth: 1,
    borderColor: "#1E2A35",
  },

  aiIcon: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: "#1D2B37",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  aiIconText: {
    color: "#6FC5FF",
    fontSize: 20,
  },

  aiContent: {
    flex: 1,
  },

  aiTitle: {
    color: "#E7EBF0",
    fontSize: 13,
    fontWeight: "700",
  },

  aiSubtitle: {
    color: "#73808D",
    fontSize: 11,
    lineHeight: 17,
    marginTop: 4,
  },

  aiArrow: {
    color: "#65717E",
    fontSize: 27,
    marginLeft: 8,
  },

  feedHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },

  feedTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
  },

  feedFilter: {
    color: "#73808D",
    fontSize: 12,
  },

  post: {
    backgroundColor: "#171A20",
    borderRadius: 20,
    padding: 18,
    marginBottom: 14,
  },

  pressed: {
    opacity: 0.75,
  },

  postHeader: {
    flexDirection: "row",
    alignItems: "center",
  },

  smallAvatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: "#252A33",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 11,
  },

  avatarText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
  },

  authorInfo: {
    flex: 1,
  },

  postName: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },

  department: {
    color: "#737E8B",
    fontSize: 11,
    marginTop: 2,
  },

  more: {
    color: "#6C7682",
    fontSize: 13,
  },

  postText: {
    color: "#DCE1E7",
    fontSize: 14,
    lineHeight: 21,
    marginTop: 18,
  },

  postFooter: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 18,
  },

  postStats: {
    color: "#69737F",
    fontSize: 12,
    marginRight: 16,
  },

  reply: {
    color: "#6FC5FF",
    fontSize: 11,
    marginLeft: "auto",
  },
});