import { defineStore } from 'pinia'

interface CookieConsentState {
  consentGiven: boolean
  analyticsConsent: boolean
  consentTimestamp: string | null
}

export const useCookieConsentStore = defineStore('cookieConsent', {
  state: (): CookieConsentState => ({
    consentGiven: false,
    analyticsConsent: false,
    consentTimestamp: null
  }),

  getters: {
    hasConsented: (state) => state.consentGiven,
    analyticsAllowed: (state) => state.consentGiven && state.analyticsConsent
  },

  actions: {
    acceptAll() {
      this.consentGiven = true
      this.analyticsConsent = true
      this.consentTimestamp = new Date().toISOString()
    },

    acceptNecessaryOnly() {
      this.consentGiven = true
      this.analyticsConsent = false
      this.consentTimestamp = new Date().toISOString()
    },

    resetConsent() {
      this.consentGiven = false
      this.analyticsConsent = false
      this.consentTimestamp = null
    }
  },

  persist: {
    key: 'jarvis_cookie_consent',
    pick: ['consentGiven', 'analyticsConsent', 'consentTimestamp'],
    cookieOptions: {
      maxAge: 365 * 24 * 60 * 60 // 1 year
    }
  }
})
