import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Tauri expects a fixed port during development
  server: {
    port: 5173,
    strictPort: true,
  },

  // Ensure assets are embedded (important for Tauri's asset protocol)
  build: {
    outDir: "dist",
    target: ["es2021", "chrome100", "safari13"],
    minify: !process.env.TAURI_DEBUG ? "esbuild" : false,
    sourcemap: !!process.env.TAURI_DEBUG,
  },

  // Environment variables exposed to the frontend
  envPrefix: ["VITE_", "TAURI_"],
});
