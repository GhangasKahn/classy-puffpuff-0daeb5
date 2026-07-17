import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Built output is committed to /aegis/ so the existing Netlify site
// (publish ".", no build command) serves it at https://<site>/aegis/
export default defineConfig({
  plugins: [react()],
  base: "/aegis/",
  build: {
    outDir: "../aegis",
    emptyOutDir: true,
  },
});
