import { ScrollView, Text, View, Pressable, StyleSheet, TextInput, Platform } from "react-native";
import { useState, useMemo } from "react";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";
import { KB_ARTICLES, type KBArticle } from "@/lib/data/catalog";

const CATEGORIES = ["All", "USB Creation", "Mac Recovery", "Windows Recovery", "ChromeOS", "Linux Recovery", "Technical"];

export default function KnowledgeScreen() {
  const colors = useColors();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedArticle, setSelectedArticle] = useState<KBArticle | null>(null);

  const filteredArticles = useMemo(() => {
    let articles = KB_ARTICLES;
    if (selectedCategory !== "All") {
      articles = articles.filter((a) => a.category === selectedCategory);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      articles = articles.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.summary.toLowerCase().includes(q) ||
          a.tags.some((t) => t.includes(q))
      );
    }
    return articles;
  }, [searchQuery, selectedCategory]);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "USB Creation": return "externaldrive.fill";
      case "Mac Recovery": return "desktopcomputer";
      case "Windows Recovery": return "laptopcomputer";
      case "ChromeOS": return "globe";
      case "Linux Recovery": return "terminal";
      case "Technical": return "cpu";
      default: return "book.fill";
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "USB Creation": return "#E85D04";
      case "Mac Recovery": return "#AC39FF";
      case "Windows Recovery": return "#0078D4";
      case "ChromeOS": return "#4285F4";
      case "Linux Recovery": return "#E95420";
      case "Technical": return "#656D76";
      default: return "#E85D04";
    }
  };

  if (selectedArticle) {
    return (
      <ScreenContainer>
        <ScrollView
          contentContainerStyle={{ paddingBottom: 32 }}
          showsVerticalScrollIndicator={false}
        >
          {/* Back Button */}
          <Pressable
            onPress={() => setSelectedArticle(null)}
            style={({ pressed }) => [
              styles.backBtn,
              pressed && { opacity: 0.7 },
            ]}
          >
            <IconSymbol name="arrow.left" size={20} color={colors.primary} />
            <Text style={[styles.backBtnText, { color: colors.primary }]}>Back</Text>
          </Pressable>

          {/* Article Header */}
          <View style={styles.articleHeader}>
            <View style={[styles.articleCategoryBadge, { backgroundColor: getCategoryColor(selectedArticle.category) + "18" }]}>
              <IconSymbol name={getCategoryIcon(selectedArticle.category) as any} size={14} color={getCategoryColor(selectedArticle.category)} />
              <Text style={[styles.articleCategoryText, { color: getCategoryColor(selectedArticle.category) }]}>
                {selectedArticle.category}
              </Text>
            </View>
            <Text style={[styles.articleTitle, { color: colors.foreground }]}>
              {selectedArticle.title}
            </Text>
            <Text style={[styles.articleSummary, { color: colors.muted }]}>
              {selectedArticle.summary}
            </Text>
          </View>

          {/* Article Content */}
          <View style={styles.articleBody}>
            {selectedArticle.content.split("

").map((paragraph, idx) => {
              if (paragraph.startsWith("**") && paragraph.endsWith("**")) {
                const heading = paragraph.replace(/\*\*/g, "");
                return (
                  <Text key={idx} style={[styles.articleHeading, { color: colors.foreground }]}>
                    {heading}
                  </Text>
                );
              }
              if (paragraph.startsWith("**")) {
                const heading = paragraph.split("**")[1];
                const rest = paragraph.replace(`**${heading}**`, "").trim();
                return (
                  <View key={idx}>
                    <Text style={[styles.articleHeading, { color: colors.foreground }]}>
                      {heading}
                    </Text>
                    {rest ? (
                      <Text style={[styles.articleParagraph, { color: colors.foreground }]}>
                        {rest}
                      </Text>
                    ) : null}
                  </View>
                );
              }
              if (paragraph.includes("  ") && paragraph.includes("
")) {
                return (
                  <View key={idx} style={[styles.codeBlock, { backgroundColor: colors.surface, borderColor: colors.border }]}>
                    <Text style={[styles.codeText, { color: colors.foreground }]}>
                      {paragraph}
                    </Text>
                  </View>
                );
              }
              return (
                <Text key={idx} style={[styles.articleParagraph, { color: colors.foreground }]}>
                  {paragraph}
                </Text>
              );
            })}
          </View>

          {/* Tags */}
          <View style={styles.tagsRow}>
            {selectedArticle.tags.map((tag) => (
              <View key={tag} style={[styles.tag, { backgroundColor: colors.surface, borderColor: colors.border }]}>
                <Text style={[styles.tagText, { color: colors.muted }]}>#{tag}</Text>
              </View>
            ))}
          </View>
        </ScrollView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.screenTitle, { color: colors.foreground }]}>
            Knowledge Base
          </Text>
          <Text style={[styles.screenSubtitle, { color: colors.muted }]}>
            Guides, tutorials, and troubleshooting for OS recovery and USB creation
          </Text>
        </View>

        {/* Search Bar */}
        <View style={[styles.searchBar, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <IconSymbol name="magnifyingglass" size={18} color={colors.muted} />
          <TextInput
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholder="Search articles..."
            placeholderTextColor={colors.muted}
            style={[styles.searchInput, { color: colors.foreground }]}
            returnKeyType="done"
          />
          {searchQuery.length > 0 && (
            <Pressable onPress={() => setSearchQuery("")} style={({ pressed }) => [pressed && { opacity: 0.7 }]}>
              <IconSymbol name="xmark.circle.fill" size={18} color={colors.muted} />
            </Pressable>
          )}
        </View>

        {/* Category Filter */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryRow}
        >
          {CATEGORIES.map((cat) => (
            <Pressable
              key={cat}
              onPress={() => setSelectedCategory(cat)}
              style={({ pressed }) => [
                styles.categoryBtn,
                {
                  backgroundColor: selectedCategory === cat ? colors.primary : colors.surface,
                  borderColor: selectedCategory === cat ? colors.primary : colors.border,
                },
                pressed && { opacity: 0.8 },
              ]}
            >
              <Text
                style={[
                  styles.categoryBtnText,
                  { color: selectedCategory === cat ? "#FFFFFF" : colors.muted },
                ]}
              >
                {cat}
              </Text>
            </Pressable>
          ))}
        </ScrollView>

        {/* Article List */}
        <View style={styles.section}>
          {filteredArticles.length === 0 ? (
            <View style={styles.emptyState}>
              <IconSymbol name="magnifyingglass" size={40} color={colors.muted} />
              <Text style={[styles.emptyTitle, { color: colors.foreground }]}>
                No articles found
              </Text>
              <Text style={[styles.emptyDesc, { color: colors.muted }]}>
                Try a different search term or category
              </Text>
            </View>
          ) : (
            filteredArticles.map((article) => (
              <Pressable
                key={article.id}
                onPress={() => setSelectedArticle(article)}
                style={({ pressed }) => [
                  styles.articleCard,
                  { backgroundColor: colors.surface, borderColor: colors.border },
                  pressed && { opacity: 0.8, transform: [{ scale: 0.98 }] },
                ]}
              >
                <View style={[styles.articleIconCircle, { backgroundColor: getCategoryColor(article.category) + "18" }]}>
                  <IconSymbol
                    name={getCategoryIcon(article.category) as any}
                    size={22}
                    color={getCategoryColor(article.category)}
                  />
                </View>
                <View style={styles.articleCardText}>
                  <View style={styles.articleCardCatRow}>
                    <Text style={[styles.articleCardCat, { color: getCategoryColor(article.category) }]}>
                      {article.category}
                    </Text>
                  </View>
                  <Text style={[styles.articleCardTitle, { color: colors.foreground }]} numberOfLines={2}>
                    {article.title}
                  </Text>
                  <Text style={[styles.articleCardSummary, { color: colors.muted }]} numberOfLines={2}>
                    {article.summary}
                  </Text>
                </View>
                <IconSymbol name="chevron.right" size={18} color={colors.muted} />
              </Pressable>
            ))
          )}
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    gap: 6,
  },
  screenTitle: {
    fontSize: 28,
    fontWeight: "800",
  },
  screenSubtitle: {
    fontSize: 15,
    lineHeight: 21,
  },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: 16,
    marginTop: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    padding: 0,
  },
  categoryRow: {
    paddingHorizontal: 16,
    paddingTop: 12,
    gap: 8,
  },
  categoryBtn: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 18,
    borderWidth: 1,
  },
  categoryBtnText: {
    fontSize: 13,
    fontWeight: "600",
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 16,
    gap: 10,
  },
  articleCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    gap: 12,
  },
  articleIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  articleCardText: {
    flex: 1,
    gap: 4,
  },
  articleCardCatRow: {
    flexDirection: "row",
  },
  articleCardCat: {
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  articleCardTitle: {
    fontSize: 15,
    fontWeight: "700",
    lineHeight: 20,
  },
  articleCardSummary: {
    fontSize: 13,
    lineHeight: 18,
  },
  emptyState: {
    alignItems: "center",
    paddingVertical: 40,
    gap: 8,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: "700",
  },
  emptyDesc: {
    fontSize: 14,
  },
  // Article Detail Styles
  backBtn: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 12,
    gap: 6,
  },
  backBtnText: {
    fontSize: 16,
    fontWeight: "600",
  },
  articleHeader: {
    paddingHorizontal: 20,
    paddingTop: 16,
    gap: 10,
  },
  articleCategoryBadge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    gap: 6,
  },
  articleCategoryText: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  articleTitle: {
    fontSize: 26,
    fontWeight: "800",
    lineHeight: 32,
  },
  articleSummary: {
    fontSize: 15,
    lineHeight: 22,
  },
  articleBody: {
    paddingHorizontal: 20,
    paddingTop: 20,
    gap: 14,
  },
  articleHeading: {
    fontSize: 18,
    fontWeight: "700",
    marginTop: 8,
  },
  articleParagraph: {
    fontSize: 15,
    lineHeight: 24,
  },
  codeBlock: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
  },
  codeText: {
    fontSize: 13,
    fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace",
    lineHeight: 20,
  },
  tagsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: 20,
    marginTop: 20,
    gap: 8,
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
  },
  tagText: {
    fontSize: 12,
    fontWeight: "600",
  },
});
