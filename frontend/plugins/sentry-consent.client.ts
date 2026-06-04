import * as Sentry from '@sentry/nuxt'
import { useCookieConsentStore } from '~/composables/cookieConsent'

export default defineNuxtPlugin(() => {
  const consentStore = useCookieConsentStore()

  const enablePii = () => {
    const options = Sentry.getClient()?.getOptions()
    if (options) options.sendDefaultPii = true
  }

  if (consentStore.analyticsAllowed) {
    enablePii()
    return
  }

  const unwatch = consentStore.$subscribe((_mutation, state) => {
    if (state.consentGiven && state.analyticsConsent) {
      enablePii()
      unwatch()
    }
  })
})
