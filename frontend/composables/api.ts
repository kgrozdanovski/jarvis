import { useAuthStore } from '~/store/auth'
import { useUnauthorizedHandler } from '~/composables/unauthorized'

const DEFAULT_API_BASE = 'http://localhost:8080'
const PUBLIC_ENDPOINT_PREFIXES = [
  '/user/auth/login',
  '/user/auth/lookup',
  '/user/auth/register',
  '/user/auth/send-verification',
  '/user/auth/confirm-email',
  '/user/auth/magic-link',
  '/user/auth/reset-password',
  '/user/auth/logout',
  '/auth/google/login',
  '/auth/google/link',
  '/contact',
  '/contact/enterprise',
  '/support/contact',
  '/newsletter/subscribe',
  '/newsletter/unsubscribe'
]

export async function useApiFetch(method: string, endpoint: string, body?: any) {
  const authStore = useAuthStore()
  const handleUnauthorized = useUnauthorizedHandler()
  const runtimeConfig = useRuntimeConfig()
  const baseURL = runtimeConfig.public?.apiBase || DEFAULT_API_BASE
  const payload =
    body instanceof FormData
      ? body
      : body !== undefined
        ? JSON.stringify(body)
        : undefined

  const isPublicEndpoint = PUBLIC_ENDPOINT_PREFIXES.some((prefix) => endpoint.startsWith(prefix))

  const ensureFreshToken = async () => {
    if (!isPublicEndpoint && !authStore.hasValidAccessToken()) {
      await authStore.refreshTokens()
    }
  }

  const executeRequest = async () => {
    await ensureFreshToken()
    const headers: Record<string, string> =
      body instanceof FormData ? {} : { 'Content-Type': 'application/json' }

    const accessToken = authStore.getAccessToken()
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`
    }

    const requestOptions: Record<string, any> = { method, headers, baseURL, credentials: 'include' }
    if (payload !== undefined) {
      requestOptions.body = payload
    }

    return $fetch(endpoint, requestOptions)
  }

  const attemptRequest = async (allowRefresh: boolean) => {
    try {
      const data = await executeRequest()
      return { data, error: null }
    } catch (err: any) {
      const statusCode = err?.response?.status ?? err?.statusCode
      if (!isPublicEndpoint && statusCode === 401 && allowRefresh && typeof authStore.refreshTokens === 'function') {
        const refreshed = await authStore.refreshTokens()
        if (refreshed) {
          return attemptRequest(false)
        }
      }
      if (statusCode === 401) {
        handleUnauthorized({ endpoint, method })
      }
      return { data: null, error: err }
    }
  }

  return attemptRequest(true)
}
