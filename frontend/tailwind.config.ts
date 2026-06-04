import type { Config } from 'tailwindcss'

const withOpacity =
  (variable: string) =>
  ({ opacityValue }: { opacityValue?: string } = {}) =>
    `rgb(var(${variable}) / ${opacityValue === undefined ? 1 : opacityValue})`

export default {
  darkMode: 'class',
  content: [
    './components/**/*.{js,ts,vue}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './plugins/**/*.{js,ts}',
    './app.vue',
    './error.vue',
    './content/**/*.{md,mdx,vue}',
  ],
  theme: {
    extend: {
      colors: {
        jarvisred: {
          50: withOpacity('--jarvisred-50'),
          100: withOpacity('--jarvisred-100'),
          200: withOpacity('--jarvisred-200'),
          300: withOpacity('--jarvisred-300'),
          400: withOpacity('--jarvisred-400'),
          500: withOpacity('--jarvisred-500'),
          600: withOpacity('--jarvisred-600'),
          700: withOpacity('--jarvisred-700'),
          800: withOpacity('--jarvisred-800'),
          900: withOpacity('--jarvisred-900'),
          950: withOpacity('--jarvisred-950'),
        },
      },
      // This enables accent-jarvisred-*** utilities
      accentColor: ({ theme }) => ({
        ...theme('colors'),
        jarvisred: theme('colors.jarvisred'),
      }),
      // This enables ring-jarvisred-*** utilities
     ringColor: ({ theme }) => ({
        ...theme('colors'),
        jarvisred: theme('colors.jarvisred'),
      }),
    },
  },
  plugins: [],
}
