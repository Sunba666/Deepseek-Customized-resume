/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#fafaf9',
        ink: '#1c1917',
        muted: '#78716c',
      },
    },
  },
  plugins: [],
}
