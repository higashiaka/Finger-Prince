import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Vite config for the Electron renderer process only
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist/renderer",
    rollupOptions: {
      input: "renderer/index.html",
    },
  },
  resolve: {
    alias: {
      "@shared": path.resolve(__dirname, "../shared"),
    },
  },
  server: {
    port: 5173,
  },
});
