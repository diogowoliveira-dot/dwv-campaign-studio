import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#E8392A",
        "primary-dark": "#C12E22",
        "bg-dark": "#000000",
        "card-dark": "#121212",
        surface: "#1a1a1a",
        "surface-light": "#1c1c1e",
        "border-dark": "#27272a",
        success: "#00c29f",
        warning: "#ffc300",
        danger: "#d92626",
      },
      fontFamily: {
        display: ['"Space Grotesk"', "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(232, 57, 42, 0.15)",
        "glow-lg": "0 0 40px rgba(232, 57, 42, 0.2)",
      },
    },
  },
  plugins: [],
};
export default config;
