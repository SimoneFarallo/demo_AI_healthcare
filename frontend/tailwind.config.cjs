/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#f2f9f7',
          panel: '#ffffff',
          ink: '#0f2f2a',
          teal: '#0b9f77',
          tealDark: '#0f766e',
          sky: '#e8f7f2'
        }
      },
      boxShadow: {
        soft: '0 10px 26px rgba(15, 47, 42, 0.08)',
      }
    },
  },
  plugins: [],
};
