import { useCookieConsentStore } from '~/composables/cookieConsent'

declare global {
  interface Window {
    dataLayer?: unknown[]
    gtag?: (...args: unknown[]) => void
  }
}

let gtagLoaded = false

function injectGtag(tagId: string) {
  if (gtagLoaded || typeof document === 'undefined') return
  gtagLoaded = true

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${tagId}`
  document.head.appendChild(script)

  window.dataLayer = window.dataLayer || []
  window.gtag = function (...args: unknown[]) {
    window.dataLayer!.push(args)
  }
  window.gtag('js', new Date())
  window.gtag('config', tagId, { send_page_view: false })
}

export default defineNuxtPlugin((nuxtApp) => {
  const runtimeConfig = useRuntimeConfig()
  const tagId = runtimeConfig.public?.googleTagId as string
  if (!tagId) return

  if (import.meta.server) return

  const consentStore = useCookieConsentStore()

  const trackPageView = () => {
    if (typeof window === 'undefined' || !window.gtag) return
    const pagePath = `${window.location.pathname}${window.location.search}${window.location.hash}`
    window.gtag('config', tagId, { page_path: pagePath })
  }

  const setupTracking = () => {
    injectGtag(tagId)

    nuxtApp.hook('app:mounted', () => {
      trackPageView()
    })

    nuxtApp.hook('page:finish', () => {
      trackPageView()
    })
  }

  if (consentStore.analyticsAllowed) {
    setupTracking()
    return
  }

  const unwatch = consentStore.$subscribe((_mutation, state) => {
    if (state.consentGiven && state.analyticsConsent) {
      setupTracking()
      trackPageView()
      unwatch()
    }
  })
})
