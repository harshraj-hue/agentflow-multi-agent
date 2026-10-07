import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// "/api" requests are proxied to the FastAPI backend, so the browser sees one origin.
// Locally the backend is on 127.0.0.1:8000; in Docker Compose it is http://backend:8000.
const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: proxyTarget, changeOrigin: true },
    },
  },
});
