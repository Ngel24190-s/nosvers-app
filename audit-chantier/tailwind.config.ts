import type { Config } from 'tailwindcss';

// Palette D.I. Environnement — définie une seule fois dans src/theme/tokens.css.
// Pour changer la charte : éditer tokens.css, rien d'autre.
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        di: 'var(--di-red)',
        'di-dark': 'var(--di-red-dark)',
        'di-light': 'var(--di-red-light)',
        ink: 'var(--ink)',
        paper: 'var(--paper)',
        muted: 'var(--muted)',
        line: 'var(--line)',
        ok: 'var(--ok)',
        warn: 'var(--warn)',
        na: 'var(--na)',
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
      },
      letterSpacing: {
        di: '-0.04em',
      },
    },
  },
  plugins: [],
} satisfies Config;
