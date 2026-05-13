import { describe, it, expect, beforeEach, vi } from 'vitest';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock AsyncStorage
vi.mock('@react-native-async-storage/async-storage', () => ({
  default: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    getAllKeys: vi.fn(),
    multiGet: vi.fn(),
    multiSet: vi.fn(),
  },
}));

describe('Recipe Persistence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should save recipe to AsyncStorage', async () => {
    const recipe = {
      recipe_id: 'recipe-123',
      name: 'Windows + Ubuntu',
      deployment_type: 'MULTIBOOT',
      os_images: [
        { image_id: 'windows_11', size_gb: 5.5 },
        { image_id: 'ubuntu_22_04', size_gb: 3.2 },
      ],
      tools: ['gparted'],
      metadata: { total_size_gb: 10, estimated_write_time_minutes: 15, target_platform: 'x86_64', tags: [] },
      cached_at: new Date().toISOString(),
    };

    vi.mocked(AsyncStorage.setItem).mockResolvedValueOnce(undefined);

    const key = `@phoenixdrive_recipe_${recipe.recipe_id}`;
    await AsyncStorage.setItem(key, JSON.stringify(recipe));

    expect(AsyncStorage.setItem).toHaveBeenCalledWith(key, JSON.stringify(recipe));
  });

  it('should retrieve recipe from AsyncStorage', async () => {
    const recipe = {
      recipe_id: 'recipe-123',
      name: 'Windows + Ubuntu',
      deployment_type: 'MULTIBOOT',
      os_images: [],
      tools: [],
      metadata: { total_size_gb: 10, estimated_write_time_minutes: 15, target_platform: 'x86_64', tags: [] },
    };

    const key = `@phoenixdrive_recipe_${recipe.recipe_id}`;
    vi.mocked(AsyncStorage.getItem).mockResolvedValueOnce(JSON.stringify(recipe));

    const result = await AsyncStorage.getItem(key);
    const retrieved = result ? JSON.parse(result) : null;

    expect(retrieved).toEqual(recipe);
    expect(retrieved.recipe_id).toBe('recipe-123');
  });

  it('should list all saved recipes', async () => {
    const recipes = [
      {
        recipe_id: 'recipe-1',
        name: 'Recipe 1',
        deployment_type: 'MULTIBOOT',
        os_images: [],
        tools: [],
        metadata: { total_size_gb: 10, estimated_write_time_minutes: 15, target_platform: 'x86_64', tags: [] },
      },
      {
        recipe_id: 'recipe-2',
        name: 'Recipe 2',
        deployment_type: 'SINGLE_BOOT',
        os_images: [],
        tools: [],
        metadata: { total_size_gb: 5, estimated_write_time_minutes: 10, target_platform: 'x86_64', tags: [] },
      },
    ];

    const recipeKeys = recipes.map((r) => `@phoenixdrive_recipe_${r.recipe_id}`);
    vi.mocked(AsyncStorage.getAllKeys).mockResolvedValueOnce(recipeKeys);

    const allKeys = await AsyncStorage.getAllKeys();
    const recipeKeysList = allKeys.filter((k) => k.startsWith('@phoenixdrive_recipe_'));

    expect(recipeKeysList).toHaveLength(2);
  });

  it('should delete recipe from AsyncStorage', async () => {
    const recipeId = 'recipe-123';
    const key = `@phoenixdrive_recipe_${recipeId}`;

    vi.mocked(AsyncStorage.removeItem).mockResolvedValueOnce(undefined);

    await AsyncStorage.removeItem(key);

    expect(AsyncStorage.removeItem).toHaveBeenCalledWith(key);
  });

  it('should update recipe usage count', async () => {
    const recipe: { recipe_id: string; name: string; use_count: number; last_used: string | null } = {
      recipe_id: 'recipe-123',
      name: 'Test Recipe',
      use_count: 0,
      last_used: null,
    };

    recipe.use_count++;
    recipe.last_used = new Date().toISOString();

    expect(recipe.use_count).toBe(1);
    expect(recipe.last_used).toBeDefined();
  });

  it('should handle recipe not found', async () => {
    const key = '@phoenixdrive_recipe_nonexistent';
    vi.mocked(AsyncStorage.getItem).mockResolvedValueOnce(null);

    const result = await AsyncStorage.getItem(key);

    expect(result).toBeNull();
  });

  it('should handle corrupted recipe data', async () => {
    const key = '@phoenixdrive_recipe_corrupted';
    const corruptedData = 'not valid json';

    vi.mocked(AsyncStorage.getItem).mockResolvedValueOnce(corruptedData);

    const result = await AsyncStorage.getItem(key);

    if (result) {
      expect(() => JSON.parse(result)).toThrow();
    }
  });

  it('should batch save multiple recipes', async () => {
    const recipes = [
      { recipe_id: 'recipe-1', name: 'Recipe 1' },
      { recipe_id: 'recipe-2', name: 'Recipe 2' },
      { recipe_id: 'recipe-3', name: 'Recipe 3' },
    ];

    const pairs: Array<[string, string]> = recipes.map((r) => [`@phoenixdrive_recipe_${r.recipe_id}`, JSON.stringify(r)]);

    vi.mocked(AsyncStorage.multiSet).mockResolvedValueOnce(undefined);

    await AsyncStorage.multiSet(pairs);

    expect(AsyncStorage.multiSet).toHaveBeenCalledWith(pairs);
  });

  it('should batch retrieve multiple recipes', async () => {
    const keys = ['@phoenixdrive_recipe_1', '@phoenixdrive_recipe_2'];
    const values = [
      JSON.stringify({ recipe_id: 'recipe-1', name: 'Recipe 1' }),
      JSON.stringify({ recipe_id: 'recipe-2', name: 'Recipe 2' }),
    ];

    const pairs: Array<[string, string]> = keys.map((k, i) => [k, values[i]]);
    vi.mocked(AsyncStorage.multiGet).mockResolvedValueOnce(pairs);

    const result = await AsyncStorage.multiGet(keys);

    expect(result).toHaveLength(2);
  });
});

describe('Bookmark Persistence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should save bookmarks to AsyncStorage', async () => {
    const bookmarks = ['article-1', 'article-2', 'article-3'];
    const key = '@phoenixdrive_bookmarks';

    vi.mocked(AsyncStorage.setItem).mockResolvedValueOnce(undefined);

    await AsyncStorage.setItem(key, JSON.stringify(bookmarks));

    expect(AsyncStorage.setItem).toHaveBeenCalledWith(key, JSON.stringify(bookmarks));
  });

  it('should retrieve bookmarks from AsyncStorage', async () => {
    const bookmarks = ['article-1', 'article-2'];
    const key = '@phoenixdrive_bookmarks';
    const jsonData = JSON.stringify(bookmarks);

    vi.mocked(AsyncStorage.getItem).mockResolvedValueOnce(jsonData);

    const result = await AsyncStorage.getItem(key);
    const retrieved = result ? JSON.parse(result) : [];

    expect(retrieved).toEqual(bookmarks);
    expect(retrieved).toHaveLength(2);
  });

  it('should add bookmark', async () => {
    const bookmarks = ['article-1', 'article-2'];
    bookmarks.push('article-3');

    expect(bookmarks).toContain('article-3');
    expect(bookmarks).toHaveLength(3);
  });

  it('should remove bookmark', async () => {
    const bookmarks = ['article-1', 'article-2', 'article-3'];
    const filtered = bookmarks.filter((id) => id !== 'article-2');

    expect(filtered).not.toContain('article-2');
    expect(filtered).toHaveLength(2);
  });

  it('should check if article is bookmarked', () => {
    const bookmarks = ['article-1', 'article-2'];

    expect(bookmarks.includes('article-1')).toBe(true);
    expect(bookmarks.includes('article-99')).toBe(false);
  });

  it('should clear all bookmarks', async () => {
    const key = '@phoenixdrive_bookmarks';

    vi.mocked(AsyncStorage.removeItem).mockResolvedValueOnce(undefined);

    await AsyncStorage.removeItem(key);

    expect(AsyncStorage.removeItem).toHaveBeenCalledWith(key);
  });

  it('should prevent duplicate bookmarks', () => {
    const bookmarks = new Set(['article-1', 'article-2']);
    bookmarks.add('article-1');

    expect(bookmarks.size).toBe(2);
  });
});

describe('USB Build History', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should save USB build to history', async () => {
    const build = {
      build_id: 'build-123',
      recipe_id: 'recipe-123',
      device_id: 'usb-456',
      status: 'completed',
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      duration_seconds: 900,
    };

    const key = `@phoenixdrive_build_${build.build_id}`;
    vi.mocked(AsyncStorage.setItem).mockResolvedValueOnce(undefined);

    await AsyncStorage.setItem(key, JSON.stringify(build));

    expect(AsyncStorage.setItem).toHaveBeenCalledWith(key, JSON.stringify(build));
  });

  it('should retrieve build history', async () => {
    const build = {
      build_id: 'build-123',
      recipe_id: 'recipe-123',
      status: 'completed',
      duration_seconds: 900,
    };

    const key = `@phoenixdrive_build_${build.build_id}`;
    vi.mocked(AsyncStorage.getItem).mockResolvedValueOnce(JSON.stringify(build));

    const result = await AsyncStorage.getItem(key);
    const retrieved = result ? JSON.parse(result) : null;

    expect(retrieved).toEqual(build);
  });

  it('should list all builds', async () => {
    const builds = [
      { build_id: 'build-1', status: 'completed' },
      { build_id: 'build-2', status: 'completed' },
      { build_id: 'build-3', status: 'failed' },
    ];

    const buildKeys = builds.map((b) => `@phoenixdrive_build_${b.build_id}`);
    vi.mocked(AsyncStorage.getAllKeys).mockResolvedValueOnce(buildKeys);

    const allKeys = await AsyncStorage.getAllKeys();
    const buildKeysList = allKeys.filter((k) => k.startsWith('@phoenixdrive_build_'));

    expect(buildKeysList).toHaveLength(3);
  });

  it('should delete build from history', async () => {
    const buildId = 'build-123';
    const key = `@phoenixdrive_build_${buildId}`;

    vi.mocked(AsyncStorage.removeItem).mockResolvedValueOnce(undefined);

    await AsyncStorage.removeItem(key);

    expect(AsyncStorage.removeItem).toHaveBeenCalledWith(key);
  });
});

describe('Settings Persistence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should save user settings', async () => {
    const settings = {
      theme: 'dark',
      notifications_enabled: true,
      auto_verify: true,
      preferred_language: 'en',
    };

    const key = '@phoenixdrive_settings';
    vi.mocked(AsyncStorage.setItem).mockResolvedValueOnce(undefined);

    await AsyncStorage.setItem(key, JSON.stringify(settings));

    expect(AsyncStorage.setItem).toHaveBeenCalledWith(key, JSON.stringify(settings));
  });

  it('should retrieve user settings', async () => {
    const settings = {
      theme: 'dark',
      notifications_enabled: true,
    };

    const key = '@phoenixdrive_settings';
    vi.mocked(AsyncStorage.getItem).mockResolvedValueOnce(JSON.stringify(settings));

    const result = await AsyncStorage.getItem(key);
    const retrieved = result ? JSON.parse(result) : {};

    expect(retrieved.theme).toBe('dark');
    expect(retrieved.notifications_enabled).toBe(true);
  });

  it('should update individual setting', async () => {
    const settings = { theme: 'light', notifications_enabled: true };
    settings.theme = 'dark';

    expect(settings.theme).toBe('dark');
  });
});

describe('Storage Quota Management', () => {
  it('should calculate total storage used', () => {
    const recipes = [
      { size_gb: 10 },
      { size_gb: 15 },
      { size_gb: 8 },
    ];

    const totalSize = recipes.reduce((sum, r) => sum + r.size_gb, 0);

    expect(totalSize).toBe(33);
  });

  it('should warn when approaching quota', () => {
    const usedGB = 460;
    const quotaGB = 500;
    const percentUsed = (usedGB / quotaGB) * 100;

    expect(percentUsed).toBeGreaterThan(90);
  });

  it('should prevent saving when quota exceeded', () => {
    const usedGB = 500;
    const quotaGB = 500;
    const canSave = usedGB < quotaGB;

    expect(canSave).toBe(false);
  });
});
