import { defineStore } from 'pinia'
import { type IUser } from '~/types/types'

const DEFAULT_API_BASE = 'http://localhost:8080'
let refreshPromise: Promise<boolean> | null = null
const CLOCK_SKEW_MS = 15 * 1000 // 15s safety window

const toTimestamp = (value?: string | number | null): number | null => {
  if (!value) return null
  const ts = typeof value === 'number' ? value : Date.parse(value)
  return Number.isFinite(ts) ? ts : null
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null as null | string,
    accessTokenExpiresAt: null as null | number,
    user: null as null | IUser
  }),
  actions: {
    getCurrentUser(): IUser | null {
      return this.user
    },
    getAccessToken(): string | null {
      return this.accessToken
    },
    isAccessTokenExpired(): boolean {
      if (!this.accessToken || !this.accessTokenExpiresAt) return true
      return Date.now() >= this.accessTokenExpiresAt - CLOCK_SKEW_MS
    },
    hasValidAccessToken(): boolean {
      return !!this.accessToken && !this.isAccessTokenExpired()
    },
    hasValidRefreshToken(): boolean {
      // Refresh token lives in an HttpOnly cookie, so JS cannot inspect it.
      return true
    },
    isAuthenticated(): boolean {
      return this.hasValidAccessToken()
    },
    setCurrentUser(user: IUser | null) {
      this.user = user
    },
    setAccessToken(token: string | null, expiresAt?: string | number | null) {
      this.accessToken = token
      this.accessTokenExpiresAt = token ? toTimestamp(expiresAt) : null
    },
    saveAuth(
      user: IUser,
      tokens: {
        accessToken: string
        accessTokenExpiresAt?: string | number | null
      }
    ) {
      this.setAccessToken(tokens.accessToken, tokens.accessTokenExpiresAt)
      this.setCurrentUser(user)
    },
    logout() {
      this.setCurrentUser(null)
      this.setAccessToken(null)
    },
    async refreshTokens(): Promise<boolean> {
      if (refreshPromise) {
        return refreshPromise
      }

      const runtimeConfig = useRuntimeConfig()
      const baseURL = runtimeConfig.public?.apiBase || DEFAULT_API_BASE

      refreshPromise = (async () => {
        try {
          const data: any = await $fetch('/user/auth/refresh', {
            method: 'POST',
            baseURL,
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: {}
          })

          if (!data?.access_token) {
            throw new Error('Invalid refresh response')
          }

          const user = {
            id: data.public_id ?? 1,
            email: data.email ?? '',
            name: data.name ?? '',
            isAuthenticated: true,
            tier: data.tier ?? 'inactive'
          } as IUser

          this.saveAuth(user, {
            accessToken: data.access_token,
            accessTokenExpiresAt: data.access_token_expires_at
          })
          return true
        } catch (error) {
          this.logout()
          return false
        } finally {
          refreshPromise = null
        }
      })()

      return refreshPromise
    }
  },
  persist: true
})
