import type { Config } from 'tailwindcss';

export default {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(30 20% 98%)',
        foreground: 'hsl(220 18% 16%)',
        card: 'hsl(0 0% 100%)',
        border: 'hsl(220 16% 88%)',
        muted: 'hsl(220 16% 96%)',
        accent: 'hsl(224 28% 94%)',
      },
      boxShadow: {
        soft: '0 10px 30px rgba(17, 24, 39, 0.04)',
      },
      borderRadius: {
        xl2: '1rem',
      },
    },
  },
  plugins: [],
} satisfies Config;
