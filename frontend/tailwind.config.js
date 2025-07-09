/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        primary: '#202124',
        secondary: '#5f6368',
        tertiary: '#80868b',
      },
      spacing: {
        'golden': '1.618rem',
        'golden-sm': '1rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
      },
    },
  },
  plugins: [],
}

