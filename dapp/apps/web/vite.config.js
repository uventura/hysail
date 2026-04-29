const path = require("path");
const { defineConfig } = require("vite");

module.exports = defineConfig({
  server: {
    port: 5173,
    fs: {
      allow: [path.resolve(__dirname, "../..")],
    },
  },
});
