<template>
  <div class="min-h-screen bg-neutral-50 px-6 py-12">
    <div class="mx-auto flex w-full max-w-md flex-col gap-6 rounded-lg border border-neutral-200 bg-white p-8 shadow-sm">
      <NuxtLink to="/" class="text-sm font-semibold text-neutral-600 hover:text-neutral-950">
        Jarvis
      </NuxtLink>

      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-neutral-500">Account security</p>
        <h1 class="mt-2 text-3xl font-bold text-neutral-950">Reset your password</h1>
        <p class="mt-3 text-neutral-600">
          Choose a new password for your Jarvis account.
        </p>
      </div>

      <div v-if="state === 'success'" class="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
        Password updated. Sign in with your new password to continue.
      </div>

      <form v-else class="space-y-4" @submit.prevent="submitReset">
        <div v-if="state === 'missing'">
          <label for="reset-link" class="block text-sm font-medium text-neutral-800">Reset link</label>
          <input
            id="reset-link"
            v-model.trim="manualToken"
            type="text"
            placeholder="https://.../reset-password?token=..."
            class="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none transition focus:border-neutral-900"
          />
          <button
            type="button"
            :disabled="!manualToken"
            class="mt-3 inline-flex h-11 w-full items-center justify-center rounded-md border border-neutral-300 px-4 text-sm font-semibold text-neutral-800 transition hover:border-neutral-950 disabled:cursor-not-allowed disabled:opacity-60"
            @click="adoptManualToken"
          >
            Use this link
          </button>
        </div>

        <template v-else>
          <div>
            <label for="new-password" class="block text-sm font-medium text-neutral-800">New password</label>
            <input
              id="new-password"
              v-model="password"
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
        </template>
      </form>

      <NuxtLink to="/login" class="text-center text-sm font-semibold text-neutral-600 hover:text-neutral-950">
        Back to sign in
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { definePageMeta, useRoute } from '#imports'
import { useApiFetch } from '~/composables/api'
import { toUserFriendlyErrorMessage } from '~/composables/userFacingError'

const RESET_PASSWORD_PATH = '/user/auth/reset-password'

definePageMeta({
  layout: 'login',
  requiresAuth: false,
  head: {
    title: 'Reset password - Jarvis',
    meta: [{ name: 'robots', content: 'noindex' }]
  }
})

const route = useRoute()
const token = ref('')
const manualToken = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)
const state = ref<'missing' | 'form' | 'success'>('missing')

const passwordValid = computed(() => {
  const value = password.value
  return value.length >= 8 && /[A-Za-z]/.test(value) && /\d/.test(value)
})
const passwordsMatch = computed(() => Boolean(password.value) && password.value === confirmPassword.value)

function extractToken(value: string): string {
  try {
    const url = new URL(value)
    return url.searchParams.get('token') || value
  } catch {
    return value
  }
}

function adoptManualToken() {
  token.value = extractToken(manualToken.value)
  state.value = token.value ? 'form' : 'missing'
}

async function submitReset() {
  error.value = ''
  if (!passwordValid.value || !passwordsMatch.value) {
    error.value = 'Please enter matching passwords that meet the requirements.'
    return
  }

  loading.value = true
  const { error: apiError } = await useApiFetch('POST', RESET_PASSWORD_PATH, {
    token: token.value,
    new_password: password.value
  })
  loading.value = false

  if (apiError) {
    error.value = toUserFriendlyErrorMessage(apiError)
    return
  }

  state.value = 'success'
}

onMounted(() => {
  const routeToken = typeof route.query.token === 'string' ? route.query.token : ''
  token.value = routeToken
  state.value = token.value ? 'form' : 'missing'
})
</script>
