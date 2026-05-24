import { ScrollView, Text, View, Pressable, Linking } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';
import { useState } from 'react';

interface Tutorial {
  id: string;
  title: string;
  description: string;
  duration: string;
  thumbnail: string;
  videoUrl: string;
  category: 'getting-started' | 'device-wizard' | 'usb-builder' | 'troubleshooting';
}

const TUTORIALS: Tutorial[] = [
  {
    id: 'intro-1',
    title: 'Getting Started with PhoenixDrive',
    description: 'Learn the basics of PhoenixDrive and what you can do with it.',
    duration: '3:45',
    thumbnail: '🎬',
    videoUrl: 'https://www.youtube.com/embed/placeholder1',
    category: 'getting-started',
  },
  {
    id: 'wizard-1',
    title: 'Using the Device Wizard',
    description: 'Step-by-step guide to identify your device and compatible operating systems.',
    duration: '5:20',
    thumbnail: '🎯',
    videoUrl: 'https://www.youtube.com/embed/placeholder2',
    category: 'device-wizard',
  },
  {
    id: 'builder-1',
    title: 'Building Your First USB',
    description: 'Create a bootable USB drive with your chosen operating system.',
    duration: '7:15',
    thumbnail: '💾',
    videoUrl: 'https://www.youtube.com/embed/placeholder3',
    category: 'usb-builder',
  },
  {
    id: 'bootcamp-1',
    title: 'Boot Camp Setup for Mac Users',
    description: 'Complete guide to setting up Windows on your Mac with Boot Camp.',
    duration: '8:30',
    thumbnail: '🍎',
    videoUrl: 'https://www.youtube.com/embed/placeholder4',
    category: 'getting-started',
  },
  {
    id: 'troubleshoot-1',
    title: 'Troubleshooting Common Issues',
    description: 'Solutions to frequently encountered problems and how to fix them.',
    duration: '6:45',
    thumbnail: '🔧',
    videoUrl: 'https://www.youtube.com/embed/placeholder5',
    category: 'troubleshooting',
  },
  {
    id: 'advanced-1',
    title: 'Advanced USB Recipes',
    description: 'Create complex multi-boot USB drives with multiple operating systems.',
    duration: '9:00',
    thumbnail: '⚙️',
    videoUrl: 'https://www.youtube.com/embed/placeholder6',
    category: 'usb-builder',
  },
];

export default function VideoTutorialsScreen() {
  const colors = useColors();
  const [selectedCategory, setSelectedCategory] = useState<Tutorial['category'] | 'all'>('all');

  const categories = [
    { id: 'all', label: 'All' },
    { id: 'getting-started', label: 'Getting Started' },
    { id: 'device-wizard', label: 'Device Wizard' },
    { id: 'usb-builder', label: 'USB Builder' },
    { id: 'troubleshooting', label: 'Troubleshooting' },
  ];

  const filteredTutorials =
    selectedCategory === 'all' ? TUTORIALS : TUTORIALS.filter((t) => t.category === selectedCategory);

  const handleWatchVideo = async (videoUrl: string) => {
    try {
      await Linking.openURL(videoUrl);
    } catch (err) {
      console.error('Failed to open video:', err);
    }
  };

  return (
    <ScreenContainer className="bg-background">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} showsVerticalScrollIndicator={false}>
        <View className="gap-6 pb-8">
          {/* Header */}
          <View className="gap-2">
            <Text className="text-3xl font-bold text-foreground">Video Tutorials</Text>
            <Text className="text-base text-muted">Learn PhoenixDrive step by step</Text>
          </View>

          {/* Category Filter */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: 8 }}
            className="pb-2"
          >
            {categories.map((cat) => (
              <Pressable
                key={cat.id}
                onPress={() => setSelectedCategory(cat.id as any)}
                style={({ pressed }) => [
                  {
                    backgroundColor:
                      selectedCategory === cat.id ? colors.primary : colors.surface,
                    paddingHorizontal: 16,
                    paddingVertical: 8,
                    borderRadius: 20,
                    opacity: pressed ? 0.8 : 1,
                  },
                ]}
              >
                <Text
                  className={`font-semibold ${
                    selectedCategory === cat.id ? 'text-background' : 'text-foreground'
                  }`}
                >
                  {cat.label}
                </Text>
              </Pressable>
            ))}
          </ScrollView>

          {/* Tutorial List */}
          <View className="gap-4">
            {filteredTutorials.map((tutorial) => (
              <Pressable
                key={tutorial.id}
                onPress={() => handleWatchVideo(tutorial.videoUrl)}
                style={({ pressed }) => [
                  {
                    backgroundColor: colors.surface,
                    borderRadius: 12,
                    overflow: 'hidden',
                    opacity: pressed ? 0.8 : 1,
                  },
                ]}
              >
                <View className="flex-row gap-4 p-4">
                  {/* Thumbnail */}
                  <View
                    className="w-20 h-20 rounded-lg items-center justify-center"
                    style={{ backgroundColor: colors.primary }}
                  >
                    <Text className="text-3xl">{tutorial.thumbnail}</Text>
                  </View>

                  {/* Content */}
                  <View className="flex-1 justify-between">
                    <View className="gap-1">
                      <Text className="text-lg font-semibold text-foreground">{tutorial.title}</Text>
                      <Text className="text-sm text-muted" numberOfLines={2}>
                        {tutorial.description}
                      </Text>
                    </View>
                    <Text className="text-xs text-muted">⏱️ {tutorial.duration}</Text>
                  </View>

                  {/* Play Icon */}
                  <View className="justify-center">
                    <Text className="text-2xl">▶️</Text>
                  </View>
                </View>
              </Pressable>
            ))}
          </View>

          {/* Empty State */}
          {filteredTutorials.length === 0 && (
            <View className="items-center justify-center py-12 gap-4">
              <Text className="text-4xl">🎬</Text>
              <Text className="text-lg font-semibold text-foreground">No tutorials found</Text>
              <Text className="text-sm text-muted text-center">
                Try selecting a different category
              </Text>
            </View>
          )}

          {/* Tips Section */}
          <View
            className="p-4 rounded-lg gap-3"
            style={{ backgroundColor: colors.primary + '20' }}
          >
            <Text className="font-semibold text-foreground">💡 Pro Tips</Text>
            <Text className="text-sm text-muted leading-relaxed">
              • Watch tutorials in order for best learning experience{' '}• Pause and follow along with your device{' '}• Check the Knowledge Base for written guides
            </Text>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
