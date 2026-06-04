import {computed} from 'vue'
import {useAuthStore} from '~/store/auth'
import { useUnauthorizedHandler } from '~/composables/unauthorized'

export const DEFAULT_API_BASE = 'http://localhost:8080'

export function useApiBaseUrl() {
  const runtimeConfig = useRuntimeConfig()
  return computed(() => (runtimeConfig.public?.apiBase || DEFAULT_API_BASE).replace(/\/+$/, ''))
}

export function useEnsureAccessToken() {
  const authStore = useAuthStore()
  return async () => {
    if (authStore.hasValidAccessToken()) {
      return authStore.getAccessToken()
    }
    await authStore.refreshTokens()
    if (authStore.hasValidAccessToken()) {
      return authStore.getAccessToken()
    }
    const token = authStore.getAccessToken()
    if (!token) {
      throw new Error('Authentication required to download files.')
    }
    return token
  }
}

export function useAuthenticatedFetch() {
  const apiBaseUrl = useApiBaseUrl()
  const ensureAccessToken = useEnsureAccessToken()
  const authStore = useAuthStore()
  const handleUnauthorized = useUnauthorizedHandler()

  const executeRequest = async (token: string, path: string, options: RequestInit) => {
    const headers = new Headers(options.headers || {})
    headers.set('Authorization', `Bearer ${token}`)
    const requestOptions: RequestInit = {...options, headers}
    return fetch(`${apiBaseUrl.value}${path}`, requestOptions)
  }

  return async (path: string, options: RequestInit = {}) => {
    const method = options.method || 'GET'
    let token: string
    try {
      token = await ensureAccessToken()
    } catch (error) {
      handleUnauthorized({ endpoint: path, method })
      throw error
    }

    let response = await executeRequest(token, path, options)
    if (response.status !== 401) {
      return response
    }

    const refreshed = typeof authStore.refreshTokens === 'function' ? await authStore.refreshTokens() : false
    const freshToken = refreshed && authStore.getAccessToken ? authStore.getAccessToken() : null
    if (freshToken) {
      response = await executeRequest(freshToken, path, options)
      if (response.status !== 401) {
        return response
      }
    }

    handleUnauthorized({ endpoint: path, method: options.method || 'GET' })
    return response
  }
}
