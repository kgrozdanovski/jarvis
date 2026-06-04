<template>
  <Teleport to="body">
    <transition name="fade">
      <div
        v-if="shouldShowModal"
        class="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
      >
        <div class="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-neutral-200 p-6">
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <h3 class="text-xl font-semibold text-neutral-900">Session expired</h3>
              <p class="text-sm text-neutral-600 mt-1">
                Your session has expired. Please log back in to continue where you left off.
              </p>
            </div>
          </div>

          <div class="flex flex-col sm:flex-row gap-2 mt-6">
            <button
              type="button"
              class="flex-1 rounded-full luxury-red-gradient text-white py-2.5 text-sm font-medium shadow-lg shadow-jarvisred-500/40 hover:opacity-95 transition"
              @click="handleLogin"
            >
              Log in
            </button>
            <button
              type="button"
              class="flex-1 rounded-full border border-neutral-300 text-neutral-800 py-2.5 text-sm font-medium hover:border-neutral-500 transition"
              @click="sessionRecovery.dismissSessionExpired"
            >
              Stay here
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSessionRecoveryStore } from '~/store/sessionRecovery'

const sessionRecovery = useSessionRecoveryStore()
const router = useRouter()
const route = useRoute()

const shouldShowModal = computed(
  () => sessionRecovery.sessionExpired && !(route.path || '').startsWith('/login')
)

const handleLogin = () => {
  sessionRecovery.redirectToLogin(router, route.fullPath || '/')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
