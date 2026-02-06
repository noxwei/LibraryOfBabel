import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Dark Mode Primary
        bg: {
          primary: '#0f0f1a',
          card: '#1e1e2e',
          hover: '#2a2a3e',
        },
        text: {
          primary: '#e5e5e5',
          secondary: '#a0a0a0',
        },
        // AI Model Colors
        model: {
          technical: '#7c3aed',    // Purple - Technical (granite)
          creative: '#e94560',     // Coral - Creative (bge-m3)
          multilingual: '#22c55e', // Green - Multilingual (mxbai)
          general: '#3b82f6',      // Blue - General (nomic)
          specialized: '#f59e0b',  // Amber - Specialized (snowflake)
        },
        // Relevance Indicators
        relevance: {
          high: '#22c55e',   // >90%
          medium: '#eab308', // 70-90%
          low: '#ef4444',    // <70%
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        xs: '4px',
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '24px',
        '2xl': '32px',
      },
      animation: {
        'shimmer': 'shimmer 1.5s infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}
export default config
