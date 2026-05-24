import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useState } from 'react';

/**
 * Generic hook for AsyncStorage persistence
 * Handles get, set, remove, and clear operations with error handling
 */
export function useAsyncStorage<T>(key: string, initialValue?: T) {
  const [value, setValue] = useState<T | null>(initialValue ?? null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Load from storage on mount
  useEffect(() => {
    const loadValue = async () => {
      try {
        setIsLoading(true);
        const stored = await AsyncStorage.getItem(key);
        if (stored) {
          setValue(JSON.parse(stored));
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    loadValue();
  }, [key]);

  // Save value to storage
  const saveValue = useCallback(
    async (newValue: T) => {
      try {
        setValue(newValue);
        await AsyncStorage.setItem(key, JSON.stringify(newValue));
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      }
    },
    [key]
  );

  // Remove value from storage
  const removeValue = useCallback(async () => {
    try {
      setValue(null);
      await AsyncStorage.removeItem(key);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    }
  }, [key]);

  // Clear all storage
  const clearAll = useCallback(async () => {
    try {
      setValue(null);
      await AsyncStorage.clear();
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    }
  }, []);

  return { value, isLoading, error, saveValue, removeValue, clearAll };
}

/**
 * Hook for managing recipe persistence
 */
export function useRecipePersistence() {
  const { value: recipes, saveValue, removeValue } = useAsyncStorage<Record<string, any>>('recipes', {});

  const addRecipe = useCallback(
    async (id: string, recipe: any) => {
      const updated = { ...recipes, [id]: recipe };
      await saveValue(updated);
    },
    [recipes, saveValue]
  );

  const deleteRecipe = useCallback(
    async (id: string) => {
      const updated = { ...recipes };
      delete updated[id];
      await saveValue(updated);
    },
    [recipes, saveValue]
  );

  const getRecipe = useCallback((id: string) => recipes?.[id], [recipes]);

  const getAllRecipes = useCallback(() => Object.values(recipes || {}), [recipes]);

  return { recipes, addRecipe, deleteRecipe, getRecipe, getAllRecipes };
}

/**
 * Hook for managing bookmark persistence
 */
export function useBookmarkPersistence() {
  const { value: bookmarks, saveValue } = useAsyncStorage<string[]>('bookmarks', []);

  const addBookmark = useCallback(
    async (articleId: string) => {
      if (bookmarks && !bookmarks.includes(articleId)) {
        await saveValue([...bookmarks, articleId]);
      }
    },
    [bookmarks, saveValue]
  );

  const removeBookmark = useCallback(
    async (articleId: string) => {
      if (bookmarks) {
        await saveValue(bookmarks.filter((id) => id !== articleId));
      }
    },
    [bookmarks, saveValue]
  );

  const isBookmarked = useCallback((articleId: string) => bookmarks?.includes(articleId) ?? false, [bookmarks]);

  return { bookmarks, addBookmark, removeBookmark, isBookmarked };
}

/**
 * Hook for managing build history persistence
 */
export function useBuildHistoryPersistence() {
  const { value: history, saveValue } = useAsyncStorage<any[]>('buildHistory', []);

  const addBuild = useCallback(
    async (build: any) => {
      const updated = [build, ...(history || [])].slice(0, 50); // Keep last 50 builds
      await saveValue(updated);
    },
    [history, saveValue]
  );

  const clearHistory = useCallback(async () => {
    await saveValue([]);
  }, [saveValue]);

  return { history, addBuild, clearHistory };
}

/**
 * Hook for managing app settings persistence
 */
export function useSettingsPersistence() {
  const { value: settings, saveValue } = useAsyncStorage<Record<string, any>>('appSettings', {
    theme: 'light',
    language: 'en',
    notifications: true,
    autoBackup: true,
  });

  const updateSetting = useCallback(
    async (key: string, value: any) => {
      const updated = { ...settings, [key]: value };
      await saveValue(updated);
    },
    [settings, saveValue]
  );

  const getSetting = useCallback((key: string) => settings?.[key], [settings]);

  return { settings, updateSetting, getSetting };
}
