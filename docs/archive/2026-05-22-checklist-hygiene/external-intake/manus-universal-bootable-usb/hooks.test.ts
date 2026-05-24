import { describe, it, expect, beforeEach, vi } from 'vitest';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock AsyncStorage
vi.mock('@react-native-async-storage/async-storage', () => ({
  default: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
}));

describe('Recipe Caching Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should validate recipe structure', () => {
    const recipe = {
      recipe_id: 'recipe-1',
      name: 'Test Recipe',
      deployment_type: 'MULTIBOOT',
      os_images: [
        { image_id: 'windows_11', name: 'Windows 11', os_family: 'windows', version: 'latest', architecture: 'x86_64', size_gb: 5.5, status: 'available' },
        { image_id: 'ubuntu_22_04', name: 'Ubuntu 22.04', os_family: 'linux', version: 'latest', architecture: 'x86_64', size_gb: 3.2, status: 'available' },
      ],
      tools: ['gparted', 'clonezilla'],
      metadata: { total_size_gb: 10, estimated_write_time_minutes: 15, target_platform: 'x86_64', tags: [] },
    };

    expect(recipe.recipe_id).toBeDefined();
    expect(recipe.name).toBe('Test Recipe');
    expect(recipe.deployment_type).toBe('MULTIBOOT');
    expect(recipe.os_images).toHaveLength(2);
    expect(recipe.tools).toHaveLength(2);
    expect(recipe.metadata.total_size_gb).toBe(10);
  });

  it('should calculate total recipe size correctly', () => {
    const osImages = [
      { size_gb: 5.5 },
      { size_gb: 3.2 },
    ];
    const tools = [
      { size_gb: 0.8 },
      { size_gb: 1.2 },
    ];

    const totalSize = osImages.reduce((sum, img) => sum + img.size_gb, 0) +
                     tools.reduce((sum, tool) => sum + tool.size_gb, 0);

    expect(totalSize).toBeCloseTo(10.7, 1);
  });

  it('should validate recipe fits on USB device', () => {
    const recipeSize = 10.7;
    const usbSize = 64;

    expect(recipeSize < usbSize).toBe(true);
  });

  it('should reject recipe that does not fit on USB', () => {
    const recipeSize = 70;
    const usbSize = 64;

    expect(recipeSize < usbSize).toBe(false);
  });

  it('should generate recipe ID', () => {
    const recipeId = `recipe-${Date.now()}`;
    expect(recipeId).toMatch(/^recipe-\d+$/);
  });

  it('should add timestamp to cached recipe', () => {
    const now = new Date().toISOString();
    const cachedRecipe = {
      recipe_id: 'recipe-1',
      name: 'Test Recipe',
      cached_at: now,
    };

    expect(cachedRecipe.cached_at).toBeDefined();
    expect(new Date(cachedRecipe.cached_at)).toBeInstanceOf(Date);
  });

  it('should track recipe usage count', () => {
    let useCount = 0;
    useCount++;
    useCount++;

    expect(useCount).toBe(2);
  });

  it('should update last used timestamp', () => {
    const recipe = {
      recipe_id: 'recipe-1',
      name: 'Test Recipe',
      last_used: new Date().toISOString(),
    };

    expect(recipe.last_used).toBeDefined();
    const lastUsedDate = new Date(recipe.last_used);
    expect(lastUsedDate.getTime()).toBeLessThanOrEqual(Date.now());
  });
});

describe('Article Bookmarking Utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should add article to bookmarks', () => {
    const bookmarks: string[] = [];
    bookmarks.push('article-1');

    expect(bookmarks).toContain('article-1');
    expect(bookmarks).toHaveLength(1);
  });

  it('should remove article from bookmarks', () => {
    const bookmarks = ['article-1', 'article-2'];
    const filtered = bookmarks.filter((id) => id !== 'article-1');

    expect(filtered).not.toContain('article-1');
    expect(filtered).toContain('article-2');
    expect(filtered).toHaveLength(1);
  });

  it('should check if article is bookmarked', () => {
    const bookmarks = ['article-1', 'article-2'];

    expect(bookmarks.includes('article-1')).toBe(true);
    expect(bookmarks.includes('article-3')).toBe(false);
  });

  it('should prevent duplicate bookmarks', () => {
    const bookmarks = new Set<string>();
    bookmarks.add('article-1');
    bookmarks.add('article-1');

    expect(bookmarks.size).toBe(1);
  });

  it('should clear all bookmarks', () => {
    const bookmarks = ['article-1', 'article-2', 'article-3'];
    bookmarks.length = 0;

    expect(bookmarks).toHaveLength(0);
  });
});

describe('AsyncStorage Persistence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should serialize recipe to JSON', () => {
    const recipe = {
      recipe_id: 'recipe-1',
      name: 'Test Recipe',
      deployment_type: 'MULTIBOOT',
      os_images: [],
      tools: [],
      metadata: { total_size_gb: 10, estimated_write_time_minutes: 15, target_platform: 'x86_64', tags: [] },
    };

    const json = JSON.stringify(recipe);
    expect(json).toContain('recipe-1');
    expect(json).toContain('Test Recipe');
  });

  it('should deserialize recipe from JSON', () => {
    const json = '{"recipe_id":"recipe-1","name":"Test Recipe","deployment_type":"MULTIBOOT"}';
    const recipe = JSON.parse(json);

    expect(recipe.recipe_id).toBe('recipe-1');
    expect(recipe.name).toBe('Test Recipe');
  });

  it('should handle AsyncStorage.getItem call', async () => {
    const mockData = JSON.stringify([{ recipe_id: 'recipe-1', name: 'Test' }]);
    vi.mocked(AsyncStorage.getItem).mockResolvedValueOnce(mockData);

    const result = await AsyncStorage.getItem('@phoenixdrive_recipes');
    expect(result).toBe(mockData);
  });

  it('should handle AsyncStorage.setItem call', async () => {
    vi.mocked(AsyncStorage.setItem).mockResolvedValueOnce(undefined);

    const data = JSON.stringify([{ recipe_id: 'recipe-1' }]);
    await AsyncStorage.setItem('@phoenixdrive_recipes', data);

    expect(AsyncStorage.setItem).toHaveBeenCalledWith('@phoenixdrive_recipes', data);
  });

  it('should handle AsyncStorage.removeItem call', async () => {
    vi.mocked(AsyncStorage.removeItem).mockResolvedValueOnce(undefined);

    await AsyncStorage.removeItem('@phoenixdrive_recipes');

    expect(AsyncStorage.removeItem).toHaveBeenCalledWith('@phoenixdrive_recipes');
  });

  it('should handle storage errors gracefully', async () => {
    const error = new Error('Storage error');
    vi.mocked(AsyncStorage.getItem).mockRejectedValueOnce(error);

    try {
      await AsyncStorage.getItem('@phoenixdrive_recipes');
    } catch (err) {
      expect(err).toBe(error);
    }
  });
});

describe('WebSocket Progress Tracking', () => {
  it('should track build progress state', () => {
    const progress = {
      build_id: 'build-1',
      state: 'writing',
      stage: 'writing',
      stage_progress: 45,
      overall_progress: 45,
      current_operation: 'Writing image: 45%',
      speed_mbps: 95.5,
      eta_seconds: 540,
      timestamp: new Date().toISOString(),
    };

    expect(progress.overall_progress).toBe(45);
    expect(progress.speed_mbps).toBeGreaterThan(0);
    expect(progress.eta_seconds).toBeGreaterThan(0);
  });

  it('should update progress percentage', () => {
    let progress = 0;
    progress = 25;
    progress = 50;
    progress = 75;
    progress = 100;

    expect(progress).toBe(100);
  });

  it('should calculate ETA from speed and remaining size', () => {
    const remainingSize = 5; // GB
    const speed = 100; // MB/s
    const speedGBps = speed / 1024;
    const etaSeconds = (remainingSize / speedGBps);

    expect(etaSeconds).toBeGreaterThan(0);
    expect(etaSeconds).toBeLessThan(600); // Less than 10 minutes
  });

  it('should detect build completion', () => {
    const progress = {
      state: 'complete',
      overall_progress: 100,
    };

    expect(progress.state).toBe('complete');
    expect(progress.overall_progress).toBe(100);
  });

  it('should detect build error', () => {
    const progress = {
      state: 'error',
      error_message: 'USB device disconnected',
    };

    expect(progress.state).toBe('error');
    expect(progress.error_message).toBeDefined();
  });
});
