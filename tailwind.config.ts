import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Tournament night sky — deep navy with a hint of pitch green
        bg: "#070b0d",
        surface: "#0b1418",
        surface2: "#0f1c20",
        elevated: "#142932",
        line: "#1a3038",
        line2: "#284450",
        // Text
        ink: "#f6f1e3",
        muted: "#94a3a8",
        subtle: "#5d6f78",
        // WC palette: trophy gold, pitch green, host-red, host-blue
        gold: {
          400: "#facc15",
          500: "#eab308",
          600: "#ca8a04",
          700: "#a16207",
        },
        pitch: {
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
        },
        crimson: {
          400: "#f87171",
          500: "#ef4444",
          600: "#dc2626",
          700: "#b91c1c",
        },
        royal: {
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
        },
        // Functional
        good: "#10b981",
        bad: "#ef4444",
        warn: "#facc15",
        // Probability bar segments
        home: "#3b82f6",
        draw: "#a1a1aa",
        away: "#ef4444",
      },
      fontFamily: {
        sans: ['"Fira Sans"', "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
        mono: ['"Fira Code"', "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
        display: ['"Fira Sans"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -8px rgba(234, 179, 8, 0.4)",
        glowGreen: "0 0 40px -10px rgba(16, 185, 129, 0.35)",
        glowRed: "0 0 40px -10px rgba(239, 68, 68, 0.35)",
        innerHair: "inset 0 1px 0 rgba(255,255,255,0.06)",
      },
      backgroundImage: {
        "grid-faint":
          "linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)",
        // The tournament arc: USA red → trophy gold → MEX/CAN-flag green
        "gradient-cup":
          "linear-gradient(135deg, #b91c1c 0%, #eab308 45%, #059669 100%)",
        "gradient-cup-soft":
          "linear-gradient(135deg, rgba(185,28,28,0.85) 0%, rgba(234,179,8,0.9) 50%, rgba(5,150,105,0.85) 100%)",
      },
      backgroundSize: {
        grid: "32px 32px",
      },
      animation: {
        "fade-in": "fadeIn 240ms ease-out both",
        "rise": "rise 320ms cubic-bezier(0.2, 0.7, 0.2, 1) both",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        rise: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
