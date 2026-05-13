import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import path from "path";

const templateRoot = path.resolve(import.meta.dirname);

export default defineConfig({
  plugins: [react()],
  root: templateRoot,
  resolve: {
    alias: {
      "@": path.resolve(templateRoot, "client", "src"),
      "@shared": path.resolve(templateRoot, "shared"),
      "@assets": path.resolve(templateRoot, "attached_assets"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    include: [
      "client/src/**/*.test.{ts,tsx}",
      "client/src/**/*.spec.{ts,tsx}"
    ],
    // Temporarily excluding server tests due to missing DB infrastructure in CI/test environment
    exclude: [
      "server/**/*.test.ts",
      "server/**/*.spec.ts",
      "**/node_modules/**",
      "**/dist/**"
    ],
    setupFiles: ["./client/src/tests/setup.ts"],
  },
});
