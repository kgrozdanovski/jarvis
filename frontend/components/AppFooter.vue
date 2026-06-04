<template>
  <footer class="border-t border-neutral-200 bg-white">
    <div class="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 text-sm text-neutral-600 sm:px-6 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="font-semibold text-neutral-950">Jarvis</p>
        <p class="mt-1">Local-network home AI assistant.</p>
      </div>

      <div class="flex flex-wrap gap-4">
        <NuxtLink to="/privacy-policy" class="hover:text-neutral-950">Privacy</NuxtLink>
        <NuxtLink to="/tos" class="hover:text-neutral-950">Terms</NuxtLink>
        <NuxtLink to="/cookie-policy" class="hover:text-neutral-950">Cookies</NuxtLink>
        <button class="hover:text-neutral-950" @click="openCookieSettings">Cookie settings</button>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { useCookieConsentStore } from '~/composables/cookieConsent'

const openCookieSettings = () => {
  const consentStore = useCookieConsentStore()
  consentStore.resetConsent()
}
</script>
