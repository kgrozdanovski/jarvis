const siteName = 'Jarvis'

const truthyFlags = new Set(['1', 'true', 'yes', 'on'])
const rawDebugFlag = process.env.NUXT_PUBLIC_DEBUG ?? process.env.DEBUG ?? ''
const parsedDebug =
  typeof rawDebugFlag === 'string'
    ? truthyFlags.has(rawDebugFlag.toLowerCase())
    : Boolean(rawDebugFlag)

const apiBase = process.env.HTTP_API_URL ?? 'http://localhost:8080'
const socketBase = process.env.WS_API_URL ?? apiBase

const googleClientId =
  process.env.NUXT_PUBLIC_GOOGLE_CLIENT_ID ??
  process.env.GOOGLE_OAUTH_CLIENT_ID ??
  process.env.GOOGLE_AUTH_CLIENT_ID ??
  ''

const googleTagId =
  process.env.NUXT_PUBLIC_GOOGLE_TAG_ID ??
  process.env.GOOGLE_TAG_ID ??
  ''

const clarityProjectId =
  process.env.NUXT_PUBLIC_CLARITY_PROJECT_ID ??
  process.env.NUXT_CLARITY_ID ??
  process.env.CLARITY_PROJECT_ID ??
  ''

const uploadSentrySourceMaps = truthyFlags.has(
  (process.env.SENTRY_UPLOAD_SOURCEMAPS ?? '').toLowerCase()
)

// Areas that should stay SPA-only (no SSR)
const privateRoutes = [
  '/welcome',
  '/account',
  '/account/**',
  '/admin',
  '/admin/**'
]

const privateRouteRules = Object.fromEntries(
  privateRoutes.map((route) => [route, { ssr: false }])
)

const longCacheHeaders = {
  'cache-control': 'public, max-age=31536000, immutable',
  expires: 'Thu, 31 Dec 2037 23:55:55 GMT'
}

const contentSecurityPolicy = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'self'",
  "form-action 'self'",
  "img-src 'self' data: blob: https:",
  "font-src 'self' data:",
  "style-src 'self' 'unsafe-inline' https://accounts.google.com",
  "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' https://accounts.google.com https://accounts.google.com/gsi/client https://www.googletagmanager.com https://www.google-analytics.com https://www.clarity.ms https://scripts.clarity.ms",
  "connect-src 'self' https://accounts.google.com https://accounts.google.com/gsi/ http://localhost:8080 http://127.0.0.1:8080 ws://localhost:8080 ws://127.0.0.1:8080 ws://localhost:4000 https://o4511122784780289.ingest.de.sentry.io https://www.google-analytics.com https://region1.google-analytics.com https://www.clarity.ms",
  "frame-src 'self' https://accounts.google.com https://accounts.google.com/gsi/",
  "worker-src 'self' blob:",
  "upgrade-insecure-requests"
].join('; ')

export default defineNuxtConfig({
  site: {
    url: 'http://localhost:3000',
  },

  // Turn SSR ON so head() / useHead() render for bots
  ssr: true,

  // Helps with “Nuxt instance unavailable” in async/SSR contexts
  experimental: {
    asyncContext: true
  },

  routeRules: {
    ...privateRouteRules,
    '/_nuxt/**': { headers: longCacheHeaders },
    '/images/**': { headers: longCacheHeaders },
    '/**': {
      headers: {
        'strict-transport-security': 'max-age=31536000; includeSubDomains; preload',
        'x-content-type-options': 'nosniff',
        'referrer-policy': 'strict-origin-when-cross-origin',
        'x-frame-options': 'SAMEORIGIN',
        'cross-origin-opener-policy': 'same-origin-allow-popups',
        'content-security-policy': contentSecurityPolicy
      }
    }
  },

  nitro: {
    preset: 'static',
    compressPublicAssets: true,
    prerender: {
      crawlLinks: true,
      routes: []
    }
  },

  devtools: { enabled: false },

  app: {
    // Global SEO defaults – may be overridden in <page>.vue
    head: {
      htmlAttrs: {
        lang: 'en',
        dir: 'ltr'
      },
      meta: [
        { name: 'application-name', content: siteName },
        { name: 'author', content: siteName },
        { name: 'theme-color', content: '#3B6CFF' },
        {
          name: 'robots',
          content:
            'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1'
        }
      ],
      link: []
    },

    pageTransition: { name: 'page', mode: 'out-in' }
  },

  modules: [
    '@pinia/nuxt',
    'pinia-plugin-persistedstate/nuxt',
    '@sentry/nuxt/module',
    '@nuxtjs/sitemap',
  ],

  sitemap: {
    exclude: [
      ...privateRoutes,
      '/login',
      '/reset-password',
      '/verify-email',
    ],
  },

  components: [
    {
      path: '~/components'
    }
  ],

  build: {
    transpile: []
  },

  vite: {
    server: {
      watch: {
        usePolling: true
      }
    },
    vue: {}
  },

  css: [
    '~/assets/style/main.css'
  ],

  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {}
    }
  },

  runtimeConfig: {
    public: {
      apiBase,
      socketBase,
      debugMode: parsedDebug,
      googleClientId,
      googleTagId,
      GOOGLE_OAUTH_CLIENT_ID: process.env.GOOGLE_OAUTH_CLIENT_ID ?? '',
      clarityProjectId
    }
  },

  compatibilityDate: '2025-03-29',

  sentry: {
    org: 'jarvis',
    project: 'jarvis-frontend',
    sentryUrl: 'https://sentry.io/',
    release: {
      inject: false,
      create: false,
      finalize: false
    },
    sourcemaps: {
      // Keep Debug ID injection in the build, but do the network upload in CI.
      disable: uploadSentrySourceMaps ? false : 'disable-upload',
      assets: './.output/public/_nuxt/**/*.{js,map}',
      ignore: [
        './.output/server/**',
        './.nuxt/**'
      ]
    }
  },

  sourcemap: {
    client: 'hidden'
  }
})
