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
        sacred: {
          primary: '#E7D6A3',   // Creme Ouro Suave
          secondary: '#F9DF80', // Ouro Brilhante
          tertiary: '#352723',  // Café / Chocolate Escuro
          accent: '#B3965E',    // Bronze / Borda Dourada
          surface: '#2a1e1b',   // Fundo escuro suave
          card: '#42322d',      // Card elevado
          cardHover: '#4e3b35', // Card hover
          subtext: '#c9baa7',   // Texto secundário
        }
      },
      fontFamily: {
        sans: ['Segoe UI', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
};

export default config;
