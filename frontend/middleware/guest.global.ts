import { useAuthStore } from '~/store/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  if (!import.meta.client || to.path !== '/login') return

  const auth = useAuthStore()

  if (auth.hasValidAccessToken()) {
    const nextQuery = typeof to.query.next === 'string' ? to.query.next : '/account'
    return navigateTo(nextQuery)
  }

  const refreshed = await auth.refreshTokens()
  if (refreshed && auth.hasValidAccessToken()) {
    const nextQuery = typeof to.query.next === 'string' ? to.query.next : '/account'
    return navigateTo(nextQuery)
  }
})
