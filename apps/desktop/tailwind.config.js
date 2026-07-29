/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        body: ["Outfit", "system-ui", "sans-serif"],
      },
      colors: {
        vap: {
          magenta: "#ff2bd6",
          cyan: "#2de2e6",
          peach: "#ff9f7a",
          night: "#12081f",
          ink: "#f7f2ff",
        },
      },
      keyframes: {
        "step-pulse": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(45, 226, 230, 0.35)" },
          "50%": { boxShadow: "0 0 0 8px rgba(45, 226, 230, 0)" },
        },
      },
    },
  },
  plugins: [],
};
