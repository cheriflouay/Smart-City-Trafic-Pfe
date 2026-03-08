/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        capgemini: {
          // Primary Palette
          blue: '#0058AB',
          lightBlue: '#1DB8F2',
          darkBlue: '#121A38',
          white: '#FFFFFF',
          // Secondary Palette
          turquoise: '#00D5D0',
          yellow: '#FEB100',
          orange: '#FF816E',
          lilac: '#D4D3F1',
          teal: '#00828E',
          terracotta: '#BE4D00',
          deepRed: '#8F3237',
          purple: '#71609E',
          // UI Background (Soft gray for contrast)
          grayBg: '#F5F6F8'
        }
      }
    },
  },
  plugins: [],
}