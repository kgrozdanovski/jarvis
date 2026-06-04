import { type IUser } from '~/types/types'
import { useAuthStore } from '~/store/auth'

type Session = { userId: string; email?: string; name?: string; picture?: string }

export const useAuth = () => {
  const authStore = useAuthStore()
  const session = useState<Session | null>('session', () => null)
  const apiBase = useRuntimeConfig().public.apiBase

  async function handleSuccessfulLogin(response: any) {
    try {
      const user = {
        id: response.public_id ?? 1,
        email: response.email ?? '',
        name: response.name ?? '',
        isAuthenticated: true,
        tier: response.tier ?? 'inactive'
      } as IUser

      authStore.saveAuth(user, {
        accessToken: response.access_token,
        accessTokenExpiresAt: response.access_token_expires_at
      })
    } catch (e) {
      console.error('Failed to process login response', e)
    }
  }

  async function signOut() {
    await $fetch(`${apiBase}/user/auth/logout`, { method: 'POST', credentials: 'include' })
    session.value = null
    authStore.logout()
  }

  return { session, signOut, handleSuccessfulLogin }
}
