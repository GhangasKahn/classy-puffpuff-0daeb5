/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        night: "#0A0F1E",   // ground — the night atmosphere
        deep: "#070B16",    // darkest — footer, manifesto
        surface: "#101A30", // cards
        line: "#1D2A47",
        ink: "#EAF0FA",
        muted: "#93A4C4",
        ember: "#FF6B3D",   // signal — fire, urgency, the one hot accent
        air: "#22D3EE",     // clean air — continuity with the instrument app
      },
      fontFamily: {
        sans: ['"Archivo"', "system-ui", "sans-serif"],
        drama: ['"Fraunces"', "Georgia", "serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "1.125rem", // Sage/Ruler radius language: precise, not soft
      },
      transitionTimingFunction: {
        magnetic: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [],
};
