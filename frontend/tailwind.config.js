/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        grade: {
          5: '#22c55e',  // 最高 - green-500
          4: '#86efac',  // 優良 - green-300
          3: '#fbbf24',  // 良好 - amber-400
          2: '#fb923c',  // 普通 - orange-400
          1: '#f87171',  // 不良 - red-400
          0: '#dc2626',  // 不適切 - red-600
        },
      },
    },
  },
  plugins: [],
}
