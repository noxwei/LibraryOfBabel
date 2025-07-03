/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Borgesian color palette
        'infinite-depths': {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155'
        },
        'ancient-gold': {
          900: '#92400e',
          800: '#a16207',
          700: '#ca8a04',
          600: '#eab308'
        },
        'mystic-silver': {
          600: '#64748b',
          500: '#94a3b8',
          400: '#cbd5e1'
        },
        'parchment': {
          50: '#fef7ed',
          100: '#fef3c7',
          200: '#fde68a'
        },
        'crimson-secrets': {
          800: '#991b1b',
          700: '#dc2626',
          600: '#ef4444'
        }
      },
      fontFamily: {
        'sacred': ['Cinzel', 'serif'],
        'manuscript': ['EB Garamond', 'serif'],
        'mystical': ['UnifrakturCook', 'cursive'],
        'modern': ['Inter', 'sans-serif']
      },
      animation: {
        'dust-float': 'dustFloat 10s infinite linear',
        'mystical-reveal': 'mysticalReveal 0.6s ease-out',
        'hexagonal-pulse': 'hexagonalPulse 2s infinite',
        'sacred-glow': 'sacredGlow 3s ease-in-out infinite alternate'
      },
      keyframes: {
        dustFloat: {
          '0%': { transform: 'translateY(100vh)' },
          '100%': { transform: 'translateY(-100vh)' }
        },
        mysticalReveal: {
          '0%': { 
            opacity: '0', 
            transform: 'translateY(20px) scale(0.95)' 
          },
          '100%': { 
            opacity: '1', 
            transform: 'translateY(0) scale(1)' 
          }
        },
        hexagonalPulse: {
          '0%, 100%': { transform: 'scale(1) rotate(0deg)' },
          '50%': { transform: 'scale(1.1) rotate(180deg)' }
        },
        sacredGlow: {
          '0%': { textShadow: '0 0 20px rgba(161, 98, 7, 0.3)' },
          '100%': { textShadow: '0 0 30px rgba(161, 98, 7, 0.6)' }
        }
      },
      clipPath: {
        hexagon: 'polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%)'
      }
    },
  },
  plugins: [
    function({ addUtilities }) {
      const newUtilities = {
        '.clip-hexagon': {
          'clip-path': 'polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%)'
        },
        '.mystical-shadow': {
          'box-shadow': '0 0 30px rgba(161, 98, 7, 0.2)'
        },
        '.sacred-border': {
          'border': '2px solid #a16207',
          'border-image': 'linear-gradient(45deg, #a16207, #ca8a04) 1'
        }
      }
      addUtilities(newUtilities)
    }
  ],
}