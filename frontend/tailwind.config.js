/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        sa: {
          50: '#f0f4ff',
          100: '#dbe4fe',
          200: '#bfcffc',
          300: '#93adf9',
          400: '#6b8bf5',
          500: '#4a6cf7',
          600: '#2e4cd4',
          700: '#1f3864',
          800: '#1a2d52',
          900: '#0f1b33',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}
