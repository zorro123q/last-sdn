// Vite 配置保持尽量简单，同时从项目根目录读取统一的 .env。
import { resolve } from "path";
import { fileURLToPath } from "url";
import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

const frontendDir = fileURLToPath(new URL(".", import.meta.url));
const projectRoot = resolve(frontendDir, "..");

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, projectRoot, "");

  return {
    envDir: projectRoot,
    plugins: [vue()],
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": {
          target: env.VITE_PROXY_TARGET || "http://localhost:8000",
          changeOrigin: true
        }
      }
    }
  };
});
