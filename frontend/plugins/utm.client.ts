export default defineNuxtPlugin(() => {
  const route = useRoute()
  const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'] as const
  const UTM_STORAGE_KEY = 'jarvis_utm'
  const UTM_TTL_DAYS = 30

  const hasUtmParams = UTM_KEYS.some(k => route.query[k])
  if (!hasUtmParams) return

  const utmData = {
    captured_at: new Date().toISOString(),
    expires_at: new Date(Date.now() + UTM_TTL_DAYS * 86400_000).toISOString(),
    params: Object.fromEntries(
      UTM_KEYS.filter(k => route.query[k]).map(k => [k, route.query[k]])
    ),
    landing_page: route.fullPath,
  }
  localStorage.setItem(UTM_STORAGE_KEY, JSON.stringify(utmData))
})
