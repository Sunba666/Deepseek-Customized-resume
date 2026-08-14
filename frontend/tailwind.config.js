/** @type {import('tailwindcss').Config} */
export default {
  // 深色模式：class 策略，由 useTheme 在 <html> 上切换 dark 类
  darkMode: 'class',
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
