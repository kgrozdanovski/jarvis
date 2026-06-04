const UTM_STORAGE_KEY = 'jarvis_utm'

interface UtmData {
  captured_at: string
  expires_at: string
  params: Record<string, string>
  landing_page: string
}

export function useUtm() {
  function getStoredUtm(): UtmData | null {
    if (import.meta.server) return null
    try {
      const raw = localStorage.getItem(UTM_STORAGE_KEY)
      if (!raw) return null
      const data: UtmData = JSON.parse(raw)
      if (new Date(data.expires_at) < new Date()) {
        localStorage.removeItem(UTM_STORAGE_KEY)
        return null
      }
      return data
    } catch {
      return null
    }
  }

  function getUtmParams(): Record<string, string> | null {
    return getStoredUtm()?.params ?? null
  }

  function clearUtm(): void {
    if (import.meta.server) return
    localStorage.removeItem(UTM_STORAGE_KEY)
  }

  return { getStoredUtm, getUtmParams, clearUtm }
}
