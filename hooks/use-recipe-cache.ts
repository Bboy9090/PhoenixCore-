/**
 * Recipe caching hook using AsyncStorage
 * Persists recipes locally so users can build the same USB multiple times
 */

import { useEffect, useState, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { DeploymentRecipe } from '@/hooks/use-phoenix-api';

const RECIPES_STORAGE_KEY = '@phoenixdrive_recipes';
const BOOKMARKS_STORAGE_KEY = '@phoenixdrive_bookmarks';

interface CachedRecipe extends DeploymentRecipe {
  cached_at: string;
  last_used?: string;
  use_count?: number;
}

interface RecipeCacheHook {
  recipes: CachedRecipe[];
  isLoading: boolean;
  error: string | null;
  saveRecipe: (recipe: DeploymentRecipe) => Promise<void>;
  deleteRecipe: (recipeId: string) => Promise<void>;
  getRecipe: (recipeId: string) => CachedRecipe | undefined;
  updateRecipeUsage: (recipeId: string) => Promise<void>;
  clearAllRecipes: () => Promise<void>;
}

export function useRecipeCache(): RecipeCacheHook {
  const [recipes, setRecipes] = useState<CachedRecipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load recipes from storage on mount
  useEffect(() => {
    loadRecipes();
  }, []);

  const loadRecipes = async () => {
    try {
      setIsLoading(true);
      const data = await AsyncStorage.getItem(RECIPES_STORAGE_KEY);
      if (data) {
        const parsed = JSON.parse(data);
        setRecipes(parsed);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to load recipes:', err);
      setError(err instanceof Error ? err.message : 'Failed to load recipes');
    } finally {
      setIsLoading(false);
    }
  };

  const saveRecipe = useCallback(
    async (recipe: DeploymentRecipe) => {
      try {
        const cachedRecipe: CachedRecipe = {
          ...recipe,
          cached_at: new Date().toISOString(),
          use_count: 0,
        };

        const updated = [...recipes];
        const existingIndex = updated.findIndex((r) => r.recipe_id === recipe.recipe_id);

        if (existingIndex >= 0) {
          // Update existing recipe
          updated[existingIndex] = cachedRecipe;
        } else {
          // Add new recipe
          updated.push(cachedRecipe);
        }

        await AsyncStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(updated));
        setRecipes(updated);
        setError(null);
      } catch (err) {
        console.error('Failed to save recipe:', err);
        setError(err instanceof Error ? err.message : 'Failed to save recipe');
        throw err;
      }
    },
    [recipes]
  );

  const deleteRecipe = useCallback(
    async (recipeId: string) => {
      try {
        const updated = recipes.filter((r) => r.recipe_id !== recipeId);
        await AsyncStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(updated));
        setRecipes(updated);
        setError(null);
      } catch (err) {
        console.error('Failed to delete recipe:', err);
        setError(err instanceof Error ? err.message : 'Failed to delete recipe');
        throw err;
      }
    },
    [recipes]
  );

  const getRecipe = useCallback(
    (recipeId: string) => {
      return recipes.find((r) => r.recipe_id === recipeId);
    },
    [recipes]
  );

  const updateRecipeUsage = useCallback(
    async (recipeId: string) => {
      try {
        const updated = recipes.map((r) => {
          if (r.recipe_id === recipeId) {
            return {
              ...r,
              last_used: new Date().toISOString(),
              use_count: (r.use_count || 0) + 1,
            };
          }
          return r;
        });

        await AsyncStorage.setItem(RECIPES_STORAGE_KEY, JSON.stringify(updated));
        setRecipes(updated);
        setError(null);
      } catch (err) {
        console.error('Failed to update recipe usage:', err);
        setError(err instanceof Error ? err.message : 'Failed to update recipe usage');
      }
    },
    [recipes]
  );

  const clearAllRecipes = useCallback(async () => {
    try {
      await AsyncStorage.removeItem(RECIPES_STORAGE_KEY);
      setRecipes([]);
      setError(null);
    } catch (err) {
      console.error('Failed to clear recipes:', err);
      setError(err instanceof Error ? err.message : 'Failed to clear recipes');
      throw err;
    }
  }, []);

  return {
    recipes,
    isLoading,
    error,
    saveRecipe,
    deleteRecipe,
    getRecipe,
    updateRecipeUsage,
    clearAllRecipes,
  };
}

/**
 * Hook for managing bookmarked articles
 */
export function useArticleBookmarks() {
  const [bookmarks, setBookmarks] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBookmarks();
  }, []);

  const loadBookmarks = async () => {
    try {
      setIsLoading(true);
      const data = await AsyncStorage.getItem(BOOKMARKS_STORAGE_KEY);
      if (data) {
        setBookmarks(JSON.parse(data));
      }
      setError(null);
    } catch (err) {
      console.error('Failed to load bookmarks:', err);
      setError(err instanceof Error ? err.message : 'Failed to load bookmarks');
    } finally {
      setIsLoading(false);
    }
  };

  const addBookmark = useCallback(
    async (articleId: string) => {
      try {
        const updated = [...new Set([...bookmarks, articleId])];
        await AsyncStorage.setItem(BOOKMARKS_STORAGE_KEY, JSON.stringify(updated));
        setBookmarks(updated);
        setError(null);
      } catch (err) {
        console.error('Failed to add bookmark:', err);
        setError(err instanceof Error ? err.message : 'Failed to add bookmark');
        throw err;
      }
    },
    [bookmarks]
  );

  const removeBookmark = useCallback(
    async (articleId: string) => {
      try {
        const updated = bookmarks.filter((id) => id !== articleId);
        await AsyncStorage.setItem(BOOKMARKS_STORAGE_KEY, JSON.stringify(updated));
        setBookmarks(updated);
        setError(null);
      } catch (err) {
        console.error('Failed to remove bookmark:', err);
        setError(err instanceof Error ? err.message : 'Failed to remove bookmark');
        throw err;
      }
    },
    [bookmarks]
  );

  const isBookmarked = useCallback(
    (articleId: string) => {
      return bookmarks.includes(articleId);
    },
    [bookmarks]
  );

  return {
    bookmarks,
    isLoading,
    error,
    addBookmark,
    removeBookmark,
    isBookmarked,
  };
}
