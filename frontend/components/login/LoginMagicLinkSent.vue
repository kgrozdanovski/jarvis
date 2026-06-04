<template>
  <div class="space-y-4">
    <div class="text-center">
      <h2 class="text-xl font-semibold text-neutral-900">Magic link sent</h2>
      <p class="text-neutral-600 mt-1">
        We emailed a sign-in link to <span class="font-medium">{{ form.email }}</span>. Open it on this device to continue.
      </p>
    </div>
    <div class="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
      <p class="text-sm text-neutral-700">Didn’t get it?</p>
      <p class="text-xs text-neutral-500">Check spam or try again after the cooldown.</p>
    </div>

    <p v-if="error" class="text-sm text-jarvisred-600 text-center">{{ error }}</p>

    <button
      type="button"
      class="w-full h-11 luxury-red-gradient !shadow-none text-white rounded-full font-medium disabled:opacity-60 disabled:cursor-not-allowed"
      :disabled="cooldown > 0 || loading"
      @click="$emit('resend')"
    >
      <span v-if="loading">Sending…</span>
      <span v-else-if="cooldown === 0">Resend link</span>
      <span v-else>Resend in {{ cooldown }}s</span>
    </button>

    <button
      type="button"
      class="w-full h-11 border border-neutral-300 rounded-full hover:border-neutral-900 transition-colors"
      @click="$emit('back')"
    >
      Back to password sign-in
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  form: { email: string }
  error: string
  loading: boolean
  cooldown: number
}>()

defineEmits<{
  (e: 'resend'): void
  (e: 'back'): void
}>()
</script>
