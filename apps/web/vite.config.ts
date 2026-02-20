import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@shared": path.resolve(__dirname, "../shared"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Forward all /api/* calls to the Python FastAPI backend
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
