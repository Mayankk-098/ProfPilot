import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import {
  useMemo,
  useState,
} from "react";

import {
  useRouter,
} from "expo-router";

import BottomNav
  from "../components/BottomNav";

import {
  TEMP_FACULTY,
  TEMP_POSTS,
  TEMP_RESOURCES,
} from "../data/communityTemp";

export default function CommunityScreen() {
  const router = useRouter();

  const [search, setSearch] =
    useState("");

  const query =
    search.trim().toLowerCase();

  const filteredFaculty =
    useMemo(() => {
      if (!query) {
        return TEMP_FACULTY;
      }

      return TEMP_FACULTY.filter(
        (faculty) =>
          faculty.name
            .toLowerCase()
            .includes(query) ||
          faculty.department
            .toLowerCase()
            .includes(query) ||
          faculty.teachingInterests.some(
            (interest) =>
              interest
                .toLowerCase()
                .includes(query)
          ) ||
          faculty.researchInterests.some(
            (interest) =>
              interest
                .toLowerCase()
                .includes(query)
          )
      );
    }, [query]);

  const filteredPosts =
    useMemo(() => {
      if (!query) {
        return TEMP_POSTS;
      }

      return TEMP_POSTS.filter(
        (post) =>
          post.author
            .toLowerCase()
            .includes(query) ||
          post.department
            .toLowerCase()
            .includes(query) ||
          post.text
            .toLowerCase()
            .includes(query)
      );
    }, [query]);

  const filteredResources =
    useMemo(() => {
      if (!query) {
        return TEMP_RESOURCES;
      }

      return TEMP_RESOURCES.filter(
        (resource) =>
          resource.title
            .toLowerCase()
            .includes(query) ||
          resource.description
            .toLowerCase()
            .includes(query) ||
          resource.sharedBy
            .toLowerCase()
            .includes(query)
      );
    }, [query]);

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={
          styles.container
        }
        showsVerticalScrollIndicator={
          false
        }
      >
        <Pressable
          onPress={() => router.back()}
        >
          <Text style={styles.back}>
            ‹
          </Text>
        </Pressable>

        <Text style={styles.title}>
          Faculty Community
        </Text>

        <Text style={styles.subtitle}>
          Connect, share and collaborate
        </Text>

        {/* SEARCH */}

        <TextInput
          style={styles.search}
          placeholder="Search faculty, posts & resources"
          placeholderTextColor="#68727D"
          value={search}
          onChangeText={setSearch}
        />

        {/* AI DISCOVERY */}

        <Pressable
          style={styles.aiCard}
          onPress={() =>
            router.push("/ai" as any)
          }
        >
          <View style={styles.aiIcon}>
            <Text
              style={styles.aiIconText}
            >
              ✦
            </Text>
          </View>

          <View style={styles.aiContent}>
            <Text style={styles.aiTitle}>
              Ask ProfPilot to find something
            </Text>

            <Text style={styles.aiText}>
              Use natural language to discover
              faculty, resources and discussions.
            </Text>
          </View>

          <Text style={styles.arrow}>
            ›
          </Text>
        </Pressable>

        {/* FACULTY */}

        <View
          style={styles.sectionHeader}
        >
          <Text
            style={styles.sectionTitle}
          >
            Faculty
          </Text>

          <Text
            style={styles.resultCount}
          >
            {filteredFaculty.length}
          </Text>
        </View>

        {filteredFaculty.length ===
        0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>
              No faculty found
            </Text>

            <Text style={styles.emptyText}>
              Try another search term.
            </Text>
          </View>
        ) : (
          filteredFaculty.map(
            (faculty) => (
              <View
                key={faculty.id}
                style={
                  styles.facultyCard
                }
              >
                <View
                  style={styles.avatar}
                >
                  <Text
                    style={
                      styles.avatarText
                    }
                  >
                    {faculty.name
                      .split(" ")
                      .map(
                        (part) =>
                          part[0]
                      )
                      .join("")
                      .slice(0, 2)}
                  </Text>
                </View>

                <Text
                  style={
                    styles.facultyName
                  }
                >
                  {faculty.name}
                </Text>

                <Text
                  style={
                    styles.department
                  }
                >
                  {faculty.department}
                </Text>

                <Text
                  style={
                    styles.interestLabel
                  }
                >
                  Teaching Interests
                </Text>

                <Text
                  style={
                    styles.interests
                  }
                >
                  {faculty.teachingInterests.join(
                    " · "
                  )}
                </Text>

                <Text
                  style={
                    styles.interestLabel
                  }
                >
                  Research Interests
                </Text>

                <Text
                  style={
                    styles.interests
                  }
                >
                  {faculty.researchInterests.join(
                    " · "
                  )}
                </Text>
              </View>
            )
          )
        )}

        {/* POSTS */}

        <Text style={styles.sectionTitle}>
          Recent Discussions
        </Text>

        {filteredPosts.length ===
        0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>
              No discussions found
            </Text>
          </View>
        ) : (
          filteredPosts.map(
            (post) => (
              <Pressable
                key={post.id}
                style={
                  styles.postCard
                }
              >
                <View
                  style={
                    styles.postHeader
                  }
                >
                  <View
                    style={
                      styles.smallAvatar
                    }
                  >
                    <Text
                      style={
                        styles.avatarText
                      }
                    >
                      {post.author
                        .split(" ")
                        .map(
                          (part) =>
                            part[0]
                        )
                        .join("")
                        .slice(0, 2)}
                    </Text>
                  </View>

                  <View
                    style={
                      styles.authorInfo
                    }
                  >
                    <Text
                      style={
                        styles.postAuthor
                      }
                    >
                      {post.author}
                    </Text>

                    <Text
                      style={
                        styles.department
                      }
                    >
                      {post.department}
                    </Text>
                  </View>
                </View>

                <Text
                  style={
                    styles.postText
                  }
                >
                  {post.text}
                </Text>

                <Text
                  style={styles.stats}
                >
                  ♡ {post.likes} · 💬{" "}
                  {post.comments}
                </Text>
              </Pressable>
            )
          )
        )}

        {/* RESOURCES */}

        <Text style={styles.sectionTitle}>
          Shared Resources
        </Text>

        {filteredResources.length ===
        0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyTitle}>
              No resources found
            </Text>
          </View>
        ) : (
          filteredResources.map(
            (resource) => (
              <Pressable
                key={resource.id}
                style={
                  styles.resourceCard
                }
              >
                <Text
                  style={
                    styles.resourceTitle
                  }
                >
                  {resource.title}
                </Text>

                <Text
                  style={
                    styles.resourceDescription
                  }
                >
                  {resource.description}
                </Text>

                <Text
                  style={styles.sharedBy}
                >
                  Shared by{" "}
                  {resource.sharedBy}
                </Text>
              </Pressable>
            )
          )
        )}

        <Text style={styles.tempNote}>
          Community data is temporarily isolated
          until backend community endpoints are available.
        </Text>

        <View
          style={{ height: 110 }}
        />
      </ScrollView>

      <BottomNav />
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
      marginTop: 5,
      marginBottom: 22,
    },

    search: {
      height: 52,
      backgroundColor: "#171A20",
      borderRadius: 15,
      paddingHorizontal: 16,
      color: "#FFFFFF",
      fontSize: 13,
      marginBottom: 14,
    },

    aiCard: {
      backgroundColor: "#121820",
      borderRadius: 19,
      padding: 16,
      flexDirection: "row",
      alignItems: "center",
      borderWidth: 1,
      borderColor: "#1E2A35",
      marginBottom: 28,
    },

    aiIcon: {
      width: 42,
      height: 42,
      borderRadius: 13,
      backgroundColor: "#1D2B37",
      justifyContent: "center",
      alignItems: "center",
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

    aiText: {
      color: "#73808D",
      fontSize: 10,
      lineHeight: 16,
      marginTop: 4,
    },

    arrow: {
      color: "#6FC5FF",
      fontSize: 25,
      marginLeft: 8,
    },

    sectionHeader: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 12,
    },

    sectionTitle: {
      color: "#FFFFFF",
      fontSize: 18,
      fontWeight: "700",
      marginBottom: 12,
      marginTop: 4,
    },

    resultCount: {
      color: "#6FC5FF",
      fontSize: 11,
    },

    facultyCard: {
      backgroundColor: "#171A20",
      borderRadius: 19,
      padding: 18,
      marginBottom: 12,
    },

    avatar: {
      width: 44,
      height: 44,
      borderRadius: 22,
      backgroundColor: "#252A33",
      justifyContent: "center",
      alignItems: "center",
    },

    smallAvatar: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: "#252A33",
      justifyContent: "center",
      alignItems: "center",
      marginRight: 10,
    },

    avatarText: {
      color: "#FFFFFF",
      fontSize: 11,
      fontWeight: "700",
    },

    facultyName: {
      color: "#FFFFFF",
      fontSize: 16,
      fontWeight: "700",
      marginTop: 12,
    },

    department: {
      color: "#737E8B",
      fontSize: 11,
      marginTop: 3,
    },

    interestLabel: {
      color: "#6FC5FF",
      fontSize: 10,
      fontWeight: "700",
      marginTop: 14,
    },

    interests: {
      color: "#CBD2D9",
      fontSize: 12,
      lineHeight: 18,
      marginTop: 4,
    },

    postCard: {
      backgroundColor: "#171A20",
      borderRadius: 19,
      padding: 18,
      marginBottom: 12,
    },

    postHeader: {
      flexDirection: "row",
      alignItems: "center",
    },

    authorInfo: {
      flex: 1,
    },

    postAuthor: {
      color: "#FFFFFF",
      fontWeight: "700",
      fontSize: 13,
    },

    postText: {
      color: "#DCE1E7",
      fontSize: 13,
      lineHeight: 21,
      marginTop: 17,
    },

    stats: {
      color: "#68727D",
      fontSize: 11,
      marginTop: 14,
    },

    resourceCard: {
      backgroundColor: "#121820",
      borderRadius: 17,
      padding: 17,
      marginBottom: 10,
      borderWidth: 1,
      borderColor: "#1E2A35",
    },

    resourceTitle: {
      color: "#FFFFFF",
      fontWeight: "700",
      fontSize: 13,
    },

    resourceDescription: {
      color: "#8994A0",
      fontSize: 11,
      lineHeight: 17,
      marginTop: 5,
    },

    sharedBy: {
      color: "#6FC5FF",
      fontSize: 10,
      marginTop: 10,
    },

    emptyCard: {
      backgroundColor: "#171A20",
      borderRadius: 17,
      padding: 18,
      marginBottom: 12,
    },

    emptyTitle: {
      color: "#FFFFFF",
      fontSize: 13,
      fontWeight: "700",
    },

    emptyText: {
      color: "#7E8794",
      fontSize: 11,
      marginTop: 4,
    },

    tempNote: {
      color: "#4F5A66",
      fontSize: 9,
      lineHeight: 14,
      marginTop: 15,
    },
  });