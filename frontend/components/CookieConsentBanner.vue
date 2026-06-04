<template>
  <Transition name="consent-slide">
    <div
      v-if="visible"
      class="fixed bottom-0 inset-x-0 z-50 border-t border-neutral-200 bg-white/95 backdrop-blur-sm shadow-[0_-4px_24px_rgba(0,0,0,0.08)]"
    >
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-12 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <!-- Text -->
        <p class="text-sm text-neutral-600 leading-relaxed flex-1">
          We use cookies to keep you logged in and understand basic Jarvis usage when analytics are enabled.
          <NuxtLink
            to="/cookie-policy"
            class="whitespace-nowrap text-neutral-800 underline underline-offset-2 hover:text-neutral-950"
          >
            Cookie Policy
          </NuxtLink>
        </p>

        <!-- Buttons -->
        <div class="flex gap-3 w-full sm:w-auto shrink-0">
          <button
            class="flex-1 rounded-md border border-neutral-300 px-5 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 sm:flex-none"
            @click="handleNecessaryOnly"
          >
            Necessary Only
          </button>
          <button
            class="flex-1 rounded-md bg-neutral-950 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-800 sm:flex-none"
            @click="handleAcceptAll"
          >
            Accept All
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useCookieConsentStore } from '~/composables/cookieConsent'

const consentStore = useCookieConsentStore()

const mounted = ref(false)
onMounted(() => { mounted.value = true })

const visible = computed(() => mounted.value && !consentStore.hasConsented)

const handleAcceptAll = () => {
  consentStore.acceptAll()
}

const handleNecessaryOnly = () => {
  consentStore.acceptNecessaryOnly()
}
</script>

<style scoped>
.consent-slide-enter-active,
.consent-slide-leave-active {
  transition: transform 0.35s ease, opacity 0.35s ease;
}
.consent-slide-enter-from,
.consent-slide-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
