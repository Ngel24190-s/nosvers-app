import type { Config } from 'tailwindcss';

// Themes 3 contextos via data-attribute (007 §FR-A-2):
// <html data-context="casa" | "nosvers" | "trabajo">
// Cada contexto define variables CSS en src/styles/themes.css.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        fg: 'var(--fg)',
        primary: 'var(--primary)',
        'primary-dark': 'var(--primary-dark)',
        accent: 'var(--accent)',
        muted: 'var(--muted)',
        border: 'var(--border)',
        'on-primary': 'var(--on-primary)',
        // alias paleta DI fija (independiente del contexto)
        'di-red': '#D62828',
        'di-red-dark': '#A91D1D',
      },
      fontFamily: {
        display: ['var(--font-display)'],
        body: ['var(--font-body)'],
        mono: ['ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      letterSpacing: {
        di: '-0.04em',
      },
    },
  },
  plugins: [],
} satisfies Config;
