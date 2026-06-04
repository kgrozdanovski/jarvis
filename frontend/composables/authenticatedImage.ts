import {useAuthenticatedFetch} from '~/composables/authenticatedFetch'

const isApiPath = (url: string) => url.startsWith('/admin/')

export function useAuthenticatedImageResolver() {
  const authenticatedFetch = useAuthenticatedFetch()
  const cache = new Map<string, string>()
  const objectUrls = new Set<string>()

  const resolveImageUrl = async (
    primaryUrl?: string | null,
    fallbackUrl?: string | null
  ): Promise<string> => {
    const candidates = [primaryUrl, fallbackUrl]
      .map((url) => (typeof url === 'string' ? url.trim() : ''))
      .filter(Boolean)

    for (const candidate of candidates) {
      if (!isApiPath(candidate)) {
        return candidate
      }

      const cached = cache.get(candidate)
      if (cached) {
        return cached
      }

      try {
        const response = await authenticatedFetch(candidate)
        if (!response.ok) {
          continue
        }
        const blob = await response.blob()
        const objectUrl = URL.createObjectURL(blob)
        cache.set(candidate, objectUrl)
        objectUrls.add(objectUrl)
        return objectUrl
      } catch {
        // Try the next candidate.
      }
    }

    return candidates[0] || ''
  }

  const clearResolvedImageUrls = () => {
    objectUrls.forEach((url) => URL.revokeObjectURL(url))
    objectUrls.clear()
    cache.clear()
  }

  return {
    resolveImageUrl,
    clearResolvedImageUrls,
  }
}
