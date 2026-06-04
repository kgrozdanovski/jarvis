import { useRoute } from '#imports'
import { useSessionRecoveryStore } from '~/store/sessionRecovery'

type UnauthorizedParams = {
  endpoint?: string
  method?: string
  redirectPath?: string | null
}

export function useUnauthorizedHandler() {
  const sessionRecovery = useSessionRecoveryStore()

  return ({ endpoint, method, redirectPath }: UnauthorizedParams) => {
    if (!import.meta.client) return

    const route = useRoute()
    const currentPath = route.fullPath || route.path || '/'

    // Do not surface the session expired modal while already on the login page.
    if ((route.path || '').startsWith('/login')) {
      return
    }

    const targetPath = redirectPath ?? currentPath
    sessionRecovery.triggerSessionExpired({
      redirectPath: targetPath,
      endpoint,
      method
    })
  }
}
