import { defineStore } from 'pinia'
import type { Router } from 'vue-router'

type SnapshotEntry = {
  data: any
  updatedAt: number
}

const cloneDeep = <T>(value: T): T => {
  try {
    // @ts-ignore - structuredClone may not exist in some environments
    if (typeof structuredClone === 'function') {
      return structuredClone(value)
    }
  } catch {
    // fall through to JSON clone
  }
  return JSON.parse(JSON.stringify(value))
}

export const useSessionRecoveryStore = defineStore('sessionRecovery', {
  state: () => ({
    sessionExpired: false,
    redirectPath: null as string | null,
    pendingAction: null as null | {
      endpoint?: string
      method?: string
      attemptedAt: number
    },
    formSnapshots: {} as Record<string, SnapshotEntry>
  }),
  actions: {
    setSnapshot(key: string, data: any) {
      this.formSnapshots[key] = {
        data: cloneDeep(data),
        updatedAt: Date.now()
      }
    },
    getSnapshot<T = any>(key: string): T | null {
      return (this.formSnapshots[key]?.data ?? null) as T | null
    },
    clearSnapshot(key: string) {
      if (this.formSnapshots[key]) {
        delete this.formSnapshots[key]
      }
    },
    triggerSessionExpired(payload: { redirectPath: string; endpoint?: string; method?: string }) {
      this.sessionExpired = true
      this.redirectPath = payload.redirectPath || this.redirectPath || '/'
      this.pendingAction = {
        endpoint: payload.endpoint,
        method: payload.method,
        attemptedAt: Date.now()
      }
    },
    dismissSessionExpired() {
      this.sessionExpired = false
      this.pendingAction = null
    },
    consumeRedirectPath(): string | null {
      const path = this.redirectPath
      this.redirectPath = null
      return path
    },
    prepareRedirectPath(fallback: string) {
      if (!this.redirectPath) {
        this.redirectPath = fallback
      }
      return this.redirectPath
    },
    redirectToLogin(router: Router, currentPath: string) {
      const target = this.prepareRedirectPath(currentPath || '/')
      this.dismissSessionExpired()
      router.push({ path: '/login', query: { next: target } })
    }
  },
  persist: {
    paths: ['redirectPath', 'formSnapshots']
  }
})
