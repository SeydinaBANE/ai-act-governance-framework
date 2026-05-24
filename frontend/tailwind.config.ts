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
        // Catégories de risque AI Act
        risk: {
          prohibited: "#dc2626",
          high: "#ea580c",
          limited: "#ca8a04",
          minimal: "#16a34a",
        },
      },
    },
  },
  plugins: [],
};

export default config;
