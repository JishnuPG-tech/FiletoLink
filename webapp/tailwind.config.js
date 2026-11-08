/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        ff: {
          bg: 'var(--ff-bg)',
          'bg-raised': 'var(--ff-bg-raised)',
          surface: 'var(--ff-surface)',
          'surface-strong': 'var(--ff-surface-strong)',
          'surface-glass': 'var(--ff-surface-glass)',
          border: 'var(--ff-border)',
          'border-strong': 'var(--ff-border-strong)',
          text: 'var(--ff-text)',
          'text-secondary': 'var(--ff-text-secondary)',
          'text-muted': 'var(--ff-text-muted)',
          accent: 'var(--ff-accent)',
          'accent-hover': 'var(--ff-accent-hover)',
          'accent-deep': 'var(--ff-accent-deep)',
          'accent-soft': 'var(--ff-accent-soft)',
          signal: 'var(--ff-signal)',
          'signal-soft': 'var(--ff-signal-soft)',
          success: 'var(--ff-success)',
          warning: 'var(--ff-warning)',
          danger: 'var(--ff-danger)',
        }
      },
      fontFamily: {
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
        display: ['"Plus Jakarta Sans"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        sans: ['"Inter"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'pulse-subtle': 'pulseSubtle 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '0.9', transform: 'scale(1)' },
          '50%': { opacity: '0.6', transform: 'scale(0.98)' },
        }
      }
    },
  },
  plugins: [],
}
