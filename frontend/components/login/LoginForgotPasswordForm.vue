<template>
  <form @submit.prevent="$emit('send')" class="space-y-4">
    <div>
      <label for="forgot-email" class="block text-sm font-medium text-neutral-800 mb-1">Email</label>
      <input
        id="forgot-email"
        v-model.trim="form.email"
        type="email"
        required
        autocomplete="email"
        inputmode="email"
        placeholder="you@brand.com"
        class="input-base pr-16 autofill-fix rounded-xl border border-neutral-200
               focus:border-neutral-600 focus:outline-none focus:ring-0 transition-colors"
      />
    </div>

    <p v-if="sent" class="text-sm text-emerald-600">
      If an account exists for that email, we sent a reset link.
    </p>
    <p v-if="error" class="text-sm text-jarvisred-600">{{ error }}</p>

    <button
      type="submit"
      :disabled="loading || cooldown > 0 || !form.email"
      class="w-full h-12 mt-2 luxury-red-gradient !shadow-none text-white rounded-full text-lg font-medium transition-all duration-300 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <span v-if="loading">Sending…</span>
      <span v-else-if="cooldown === 0">Send reset link</span>
      <span v-else>Resend in {{ cooldown }}s</span>
    </button>

    <button
      type="button"
      class="w-full h-11 border border-neutral-300 rounded-full hover:border-neutral-900 transition-colors"
      @click="$emit('back')"
    >
      Back to sign in
    </button>
  </form>
</template>

<script setup lang="ts">
defineProps<{
  form: { email: string }
  loading: boolean
  cooldown: number
  sent: boolean
  error: string
}>()

defineEmits<{
  (e: 'send'): void
  (e: 'back'): void
}>()
</script>
