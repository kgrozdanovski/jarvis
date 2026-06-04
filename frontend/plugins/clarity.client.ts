import { useCookieConsentStore } from '~/composables/cookieConsent'

declare global {
  interface Window {
    clarity?: (...args: unknown[]) => void
  }
}

let loaded = false

function loadClarity(projectId: string) {
  if (loaded || typeof window === 'undefined') return
  loaded = true

  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.clarity.ms/tag/${projectId}`
  document.head.appendChild(script)

  // Clarity bootstrap snippet
  ;(function (w: Window) {
    w.clarity = w.clarity || function (...args: unknown[]) {
      ;(w.clarity as any).q = (w.clarity as any).q || []
      ;(w.clarity as any).q.push(args)
    }
  })(window)
}

export default defineNuxtPlugin(() => {
  const runtimeConfig = useRuntimeConfig()
  const projectId = runtimeConfig.public?.clarityProjectId as string
  if (!projectId) return

  const consentStore = useCookieConsentStore()

  if (consentStore.analyticsAllowed) {
    loadClarity(projectId)
    return
  }

  const unwatch = consentStore.$subscribe((_mutation, state) => {
    if (state.consentGiven && state.analyticsConsent) {
      loadClarity(projectId)
      unwatch()
    }
  })
})
