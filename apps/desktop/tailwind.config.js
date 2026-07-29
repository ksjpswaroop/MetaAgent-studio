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
          magenta: "#0a66c2",
          cyan: "#378fe9",
          peach: "#915907",
          night: "#eef3f8",
          ink: "#191919",
        },
        li: {
          blue: "#0a66c2",
          dark: "#004182",
          soft: "#378fe9",
          sky: "#70b5f9",
          surface: "#eef3f8",
          ink: "#191919",
        },
      },
      keyframes: {
        "step-pulse": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(10, 102, 194, 0.28)" },
          "50%": { boxShadow: "0 0 0 8px rgba(10, 102, 194, 0)" },
        },
      },
    },
  },
  plugins: [],
};
