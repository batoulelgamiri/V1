/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'rgb(var(--color-canvas) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        elevated: 'rgb(var(--color-elevated) / <alpha-value>)',
        ink: 'rgb(var(--color-ink) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
        line: 'rgb(var(--color-line) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        success: 'rgb(var(--color-success) / <alpha-value>)',
        warning: 'rgb(var(--color-warning) / <alpha-value>)',
        danger: 'rgb(var(--color-danger) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Cascadia Code', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        panel: '0 18px 60px rgb(0 0 0 / var(--shadow-opacity))',
        glow: '0 0 28px rgb(var(--color-accent) / 0.14)',
      },
      animation: {
        'scan-slow': 'scan 8s linear infinite',
        'pulse-soft': 'pulseSoft 2.4s ease-in-out infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '15%': { opacity: '.35' },
          '85%': { opacity: '.25' },
          '100%': { transform: 'translateY(100vh)', opacity: '0' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '.55' },
          '50%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

