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
  ],
  theme: {
    extend: {
      colors: {
        jarvisblue: {
          400: withOpacity('--jarvisblue-400'),
          500: withOpacity('--jarvisblue-500'),
          600: withOpacity('--jarvisblue-600'),
        },
        jarvisviolet: {
          400: withOpacity('--jarvisviolet-400'),
          500: withOpacity('--jarvisviolet-500'),
          600: withOpacity('--jarvisviolet-600'),
        },
      },
      // This enables accent-jarvisblue-*** utilities
      accentColor: ({ theme }) => ({
        ...theme('colors'),
        jarvisblue: theme('colors.jarvisblue'),
      }),
      // This enables ring-jarvisblue-*** utilities
     ringColor: ({ theme }) => ({
        ...theme('colors'),
        jarvisblue: theme('colors.jarvisblue'),
      }),
    },
  },
  plugins: [],
}
