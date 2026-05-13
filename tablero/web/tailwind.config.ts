import type { Config } from 'tailwindcss';
// eslint-disable-next-line @typescript-eslint/no-require-imports
const animatePlugin = require('tailwindcss-animate');

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
    // Tremor JS para que sus classnames sobrevivan al tree-shake
    './node_modules/@tremor/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
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
        // Cockpit Mission Control
        cockpit: {
          bg: '#0a0a0f',
          panel: '#13131a',
          panelHi: '#1a1a23',
          border: 'rgba(255,255,255,0.06)',
          borderHi: 'rgba(255,255,255,0.12)',
          dim: '#6b7280',
          text: '#e5e7eb',
          textDim: '#9ca3af',
        },
        accent: {
          green: '#34d399',
          orange: '#fb923c',
          violet: '#a78bfa',
          red: '#ef4444',
          cyan: '#22d3ee',
          amber: '#fbbf24',
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"DM Sans"', 'system-ui', 'sans-serif'],
        editorial: ['"DM Serif Display"', 'Georgia', 'serif'],
        ui: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      backdropBlur: {
        xl: '24px',
        '2xl': '40px',
      },
      keyframes: {
        'pulse-led': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.55', transform: 'scale(0.92)' },
        },
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 0 rgba(239,68,68,0)' },
          '50%': { boxShadow: '0 0 28px rgba(239,68,68,0.55)' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'pulse-led': 'pulse-led 1.8s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 2.4s ease-in-out infinite',
        'fade-in-up': 'fade-in-up 0.4s ease-out both',
      },
    },
  },
  plugins: [animatePlugin],
};

export default config;
