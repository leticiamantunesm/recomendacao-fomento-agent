/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#04071f",
          900: "#070b2e",
          800: "#0c1238",
          700: "#121a4a",
          600: "#1a2558",
        },
        cyan: {
          DEFAULT: "#2ec7ff",
          soft: "#5ad6ff",
          muted: "rgba(46, 199, 255, 0.12)",
        },
        ink: {
          DEFAULT: "#0b1220",
          soft: "#3d4b66",
          faint: "#6b7a96",
        },
        paper: {
          DEFAULT: "#f7f8fb",
          card: "#ffffff",
          line: "#e6eaf2",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-montserrat)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(7, 11, 46, 0.04), 0 12px 32px rgba(7, 11, 46, 0.06)",
        panel: "0 24px 60px rgba(7, 11, 46, 0.12)",
      },
      maxWidth: {
        content: "1120px",
      },
    },
  },
  plugins: [],
};
