<template>
  <div class="space-y-4">
    <div class="text-center">
      <h2 class="text-xl font-semibold text-neutral-900">Confirm your email</h2>
      <p class="text-neutral-600 mt-1">
        We sent a verification link to <span class="font-medium">{{ verifyInfo.email }}</span>.
        Click the link in the email to continue.
      </p>
      <p v-if="verifying" class="text-sm text-neutral-500 mt-1">Verifying your link…</p>
    </div>

    <div class="flex gap-3">
      <button
        type="button"
        class="flex-1 h-11 border border-neutral-300 rounded-full hover:border-neutral-900 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        :disabled="resendCooldown > 0 || resendLoading"
        @click="$emit('resend')"
        :aria-busy="resendLoading"
      >
        <span v-if="resendLoading" class="inline-flex items-center gap-2 text-neutral-700">
          <svg class="w-4 h-4 animate-spin text-neutral-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke-width="4"></circle>
            <path class="opacity-75" d="M4 12a8 8 0 018-8" stroke-width="4" stroke-linecap="round"></path>
          </svg>
          Sending…
        </span>
        <span v-else-if="resendCooldown === 0">Resend email</span>
        <span v-else>Resend in {{ resendCooldown }}s</span>
      </button>
    </div>

    <div class="text-center text-sm text-neutral-600">
      Open on this device for an instant redirect.
    </div>

    <p v-if="error" class="text-sm text-jarvisred-600 text-center">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  verifyInfo: { email: string }
  verifying: boolean
  resendCooldown: number
  resendLoading: boolean
  error: string
}>()

defineEmits<{
  (e: 'resend'): void
}>()
</script>
