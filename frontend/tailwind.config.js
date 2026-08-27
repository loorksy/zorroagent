/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#0F172A",
        secondary: "#1E293B",
        accent: "#22C55E",
        desk: "#020617",
        card: "#0E1223",
        muted: "#1A1E2F",
        line: "#334155",
      },
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
