const { defineConfig } = require("vite");
const react = require("@vitejs/plugin-react");
const os = require("node:os");
const path = require("node:path");

module.exports = defineConfig({
  plugins: [react()],
  cacheDir: path.join(os.tmpdir(), "ai-seo-publisher-vite-cache"),
  server: {
    port: 5173
  }
});
