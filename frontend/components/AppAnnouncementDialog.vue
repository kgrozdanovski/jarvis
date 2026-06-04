<template>
  <transition name="fade">
    <div
      v-if="state.open"
      class="fixed inset-0 z-[5000] flex items-center justify-center bg-neutral-900/60 px-4"
    >
      <div class="max-w-lg w-full rounded-2xl bg-white shadow-2xl p-6 space-y-4">
        <div class="flex items-center gap-3">
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-700">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </span>
          <h2 class="text-lg font-semibold text-neutral-900">
            System Maintenance
          </h2>
        </div>
        <p class="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
          {{ state.message }}
        </p>
        <div class="flex justify-end">
          <button
            class="inline-flex items-center rounded-full bg-neutral-900 px-5 py-2 text-sm font-semibold text-white hover:bg-neutral-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-neutral-900"
            type="button"
            @click="dismiss"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { useAnnouncement } from '~/composables/announcement'

const { state, dismissAnnouncement } = useAnnouncement()

const dismiss = () => dismissAnnouncement()
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
