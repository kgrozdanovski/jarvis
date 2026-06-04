import { useState } from '#app'
import { computed, watch } from 'vue'
import { useRoute } from '#imports'
import { useApiFetch } from '~/composables/api'
import { useAuthStore } from '~/store/auth'

const STORAGE_PREFIX = 'jarvis:announcement:'
const ALLOWED_PREFIXES = ['/account']

type AnnouncementPayload = {
  version?: string
  message?: string
}

type AnnouncementState = {
  version: string
  message: string
  open: boolean
  loading: boolean
}

export function useAnnouncement() {
  const state = useState<AnnouncementState>('announcement-state', () => ({
    version: '',
    message: '',
    open: false,
    loading: false
  }))

  const route = useRoute()
  const authStore = useAuthStore()

  const hasWindow = () => typeof window !== 'undefined'

  const markSeen = (version: string) => {
    if (!hasWindow()) return
    window.localStorage.setItem(`${STORAGE_PREFIX}${version}`, new Date().toISOString())
  }

  const alreadySeen = (version: string) => {
    if (!hasWindow()) return false
    return window.localStorage.getItem(`${STORAGE_PREFIX}${version}`) !== null
  }

  const isAuthenticated = computed(() => authStore.isAuthenticated())

  const isEligible = computed(() => {
    if (!isAuthenticated.value) return false
    const path = route?.path || ''
    return ALLOWED_PREFIXES.some(prefix => path.startsWith(prefix))
  })

  const loadAnnouncement = async () => {
    if (!import.meta.client || state.value.loading || !isEligible.value) {
      if (!isEligible.value) {
        state.value.open = false
      }
      return
    }
    state.value.loading = true
    try {
      const { data, error } = await useApiFetch('GET', '/system/announcement')
      if (error) {
        throw error
      }
      const announcement = (data as { announcement?: AnnouncementPayload })?.announcement
      if (announcement?.version && announcement?.message && !alreadySeen(announcement.version)) {
        state.value.version = announcement.version
        state.value.message = announcement.message
        state.value.open = true
      } else {
        state.value.open = false
      }
    } catch (err) {
      console.error('Failed to load announcement', err)
      state.value.open = false
    } finally {
      state.value.loading = false
    }
  }

  const dismissAnnouncement = () => {
    if (state.value.version) {
      markSeen(state.value.version)
    }
    state.value.open = false
  }

  watch(
    () => [route?.path, isAuthenticated.value],
    () => {
      if (isEligible.value) {
        void loadAnnouncement()
      } else {
        state.value.open = false
      }
    },
    { immediate: true }
  )

  return {
    state,
    loadAnnouncement,
    dismissAnnouncement,
    isEligible
  }
}
