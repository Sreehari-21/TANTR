/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        syra: {
          primary: '#6366f1',
          dark: '#1e1b4b',
          accent: '#818cf8',
        },
      },
    },
  },
  plugins: [],
}
