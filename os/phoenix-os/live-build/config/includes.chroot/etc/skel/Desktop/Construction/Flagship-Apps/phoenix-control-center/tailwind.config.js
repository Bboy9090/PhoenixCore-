/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,tsx,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        arc: {
          bg: 'var(--arc-bg)',
          surface: 'var(--arc-surface)',
          panel: 'var(--arc-panel)',
          border: 'var(--arc-border)',
          cyan: 'var(--arc-cyan)',
          gold: 'var(--arc-gold)',
          silver: 'var(--arc-silver)',
          success: 'var(--arc-success)',
          danger: 'var(--arc-danger)',
          ember: 'var(--arc-ember)',
          blue: 'var(--arc-blue)',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'slideIn': 'slideIn 0.3s ease-out forwards',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
