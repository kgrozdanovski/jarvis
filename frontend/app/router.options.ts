import type { RouterConfig } from '@nuxt/schema'

export default <RouterConfig>{
  scrollBehavior(to, from, savedPosition) {
    // Restore on popstate (back/forward)
    if (savedPosition) {
      return savedPosition
    }
    // If navigating to a hash, let the browser/your anchor logic handle it
    if (to.hash) {
      return { el: to.hash, top: 60, behavior: 'smooth' } // keep header offset and smooth scroll
    }
    // Otherwise, always scroll to top
    return { left: 0, top: 0 }
  }
}
