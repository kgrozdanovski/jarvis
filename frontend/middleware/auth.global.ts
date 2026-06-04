import { useAuthStore } from '~/store/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  if (!import.meta.client) return

  if (!to.meta.requiresAuth) {
    return
  }

  const auth = useAuthStore()

  if (auth.hasValidAccessToken()) {
    return
  }

  const refreshed = await auth.refreshTokens()
  if (refreshed && auth.hasValidAccessToken()) {
    return
  }

  const next = encodeURIComponent(to.fullPath)
  return navigateTo(`/login?next=${next}`)
})
