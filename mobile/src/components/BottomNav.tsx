import { Pressable, StyleSheet, Text, View } from "react-native";
import { usePathname, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const tabs = [
  {
    label: "Home",
    icon: "⌂",
    route: "/home",
  },
  {
    label: "Courses",
    icon: "▣",
    route: "/courses",
  },
  {
    label: "AI",
    icon: "✦",
    route: "/ai",
  },
  {
    label: "Community",
    icon: "◉",
    route: "/community",
  },
  {
    label: "Profile",
    icon: "○",
    route: "/profile",
  },
];

export default function BottomNav() {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();

  return (
    <View
      style={[
        styles.wrapper,
        { paddingBottom: Math.max(insets.bottom, 10) },
      ]}
    >
      {tabs.map((tab) => {
        const active = pathname === tab.route;

        return (
          <Pressable
            key={tab.route}
            style={styles.tab}
            onPress={() => router.push(tab.route as any)}
          >
            <Text
              style={[
                styles.icon,
                active && styles.activeIcon,
              ]}
            >
              {tab.icon}
            </Text>

            <Text
              style={[
                styles.label,
                active && styles.activeLabel,
              ]}
            >
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#111419",
    borderTopWidth: 1,
    borderTopColor: "#20242B",
    flexDirection: "row",
    paddingTop: 10,
  },

  tab: {
    flex: 1,
    alignItems: "center",
  },

  icon: {
    color: "#68727D",
    fontSize: 21,
    marginBottom: 4,
  },

  activeIcon: {
    color: "#6FC5FF",
  },

  label: {
    color: "#68727D",
    fontSize: 10,
    fontWeight: "600",
  },

  activeLabel: {
    color: "#6FC5FF",
  },
});