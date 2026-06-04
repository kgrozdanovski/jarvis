<template>
  <form @submit.prevent="$emit('continue')" class="space-y-4">
    <div class="mb-2">
      <label for="email" class="block text-sm font-medium text-neutral-800 mb-1">Email</label>
      <input
        id="email"
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

    <p v-if="error" class="text-sm text-jarvisred-600">{{ error }}</p>

    <button
      type="submit"
      :disabled="loading || !form.email"
      class="w-full h-12 mt-2 luxury-red-gradient !shadow-none text-white rounded-full text-lg font-medium transition-all duration-300 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <span v-if="!loading">Continue</span>
      <span v-else>Checking…</span>
    </button>

    <!-- Divider -->
    <div class="relative my-6">
      <div class="absolute inset-0 flex items-center">
        <span class="w-full border-t border-neutral-200"></span>
      </div>
      <div class="relative flex justify-center">
        <span class="px-3 bg-neutral-50 text-xs uppercase tracking-wide text-neutral-500">
          or continue with Google
        </span>
      </div>
    </div>

    <!-- Google (new GIS button component; styling wrapper preserved) -->
    <div class="w-full">
      <GoogleSignInButton />
    </div>
  </form>
</template>

<script setup lang="ts">
import GoogleSignInButton from './GoogleSignInButton.vue'

defineProps<{
  form: { email: string }
  error: string
  loading: boolean
}>()

defineEmits<{
  (e: 'continue'): void
}>()
</script>
