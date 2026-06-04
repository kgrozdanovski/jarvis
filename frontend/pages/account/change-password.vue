<template>
  <div class="min-h-screen bg-neutral-50 px-6 py-12">
    <div class="mx-auto flex w-full max-w-md flex-col gap-6 rounded-lg border border-neutral-200 bg-white p-8 shadow-sm">
      <NuxtLink to="/account" class="text-sm font-semibold text-neutral-600 hover:text-neutral-950">
        Back to account
      </NuxtLink>

      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-neutral-500">Account security</p>
        <h1 class="mt-2 text-3xl font-bold text-neutral-950">Change your password</h1>
        <p class="mt-3 text-neutral-600">
          Update the password used to sign in to Jarvis.
        </p>
      </div>

      <div v-if="success" class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
        Password updated. Use the new password next time you sign in.
      </div>

      <form v-else class="space-y-4" @submit.prevent="submit">
        <div>
          <label for="current-password" class="block text-sm font-medium text-neutral-800">Current password</label>
          <input
            id="current-password"
            v-model="currentPassword"
            type="password"
            autocomplete="current-password"
            class="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none transition focus:border-neutral-900"
            required
          />
        </div>

        <div>
          <label for="new-password" class="block text-sm font-medium text-neutral-800">New password</label>
          <input
            id="new-password"
            v-model="newPassword"
            type="password"
            autocomplete="new-password"
            class="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none transition focus:border-neutral-900"
            required
          />
          <p class="mt-1 text-xs" :class="passwordValid ? 'text-emerald-700' : 'text-neutral-500'">
            Minimum 8 characters with a letter and a number.
          </p>
        </div>

        <div>
          <label for="confirm-password" class="block text-sm font-medium text-neutral-800">Confirm password</label>
          <input
            id="confirm-password"
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            class="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none transition focus:border-neutral-900"
            required
          />
        </div>

        <p v-if="error" class="text-sm text-red-700">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading || !passwordValid || !passwordsMatch"
          class="inline-flex h-11 w-full items-center justify-center rounded-md bg-neutral-950 px-4 text-sm font-semibold text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {{ loading ? 'Updating...' : 'Update password' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { definePageMeta } from '#imports'
import { useApiFetch } from '~/composables/api'
import { toUserFriendlyErrorMessage } from '~/composables/userFacingError'

definePageMeta({
  layout: 'login',
  requiresAuth: true,
  head: {
    title: 'Change password - Jarvis',
    meta: [{ name: 'robots', content: 'noindex' }]
  }
})

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const passwordValid = computed(() => {
  const value = newPassword.value
  return value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value)
})
const passwordsMatch = computed(() => Boolean(newPassword.value) && newPassword.value === confirmPassword.value)

async function submit() {
  error.value = ''
  if (!passwordValid.value || !passwordsMatch.value) {
    error.value = 'Please enter matching passwords that meet the requirements.'
    return
  }

  loading.value = true
  const { error: apiError } = await useApiFetch('POST', '/user/account/change-password', {
    current_password: currentPassword.value,
    new_password: newPassword.value
  })
  loading.value = false

  if (apiError) {
    error.value = toUserFriendlyErrorMessage(apiError)
    return
  }

  success.value = true
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}
</script>
