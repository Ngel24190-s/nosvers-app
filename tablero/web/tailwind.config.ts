import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        cream: '#FEFAF4',
        verde: {
          DEFAULT: '#5A7A2E',
          dark: '#3D6B20',
        },
        tinta: '#1c1510',
        // Author accent
        angel: '#5A7A2E',
        africa: '#C97B3A',
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        editorial: ['"DM Serif Display"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};

export default config;
