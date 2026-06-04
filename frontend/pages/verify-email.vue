<template>
  <div class="min-h-screen bg-neutral-50 px-6 py-12">
    <div class="mx-auto flex w-full max-w-md flex-col gap-6 rounded-lg border border-neutral-200 bg-white p-8 shadow-sm">
      <NuxtLink to="/" class="text-sm font-semibold text-neutral-600 hover:text-neutral-950">
        Jarvis
      </NuxtLink>

      <div>
        <p class="text-xs font-semibold uppercase tracking-wide text-neutral-500">Email verification</p>
        <h1 class="mt-2 text-3xl font-bold text-neutral-950">{{ heading }}</h1>
        <p class="mt-3 text-neutral-600">{{ message }}</p>
      </div>

      <form v-if="state === 'error'" class="space-y-4" @submit.prevent="manuallyVerify">
        <div>
          <label for="verification-link" class="block text-sm font-medium text-neutral-800">Verification link</label>
          <input
            id="verification-link"
            v-model.trim="manualToken"
            type="text"
            placeholder="https://.../verify-email?token=..."
            class="mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm outline-none transition focus:border-neutral-900"
          />
        </div>

        <button
          type="submit"
          :disabled="verifying || !manualToken"
          class="inline-flex h-11 w-full items-center justify-center rounded-md bg-neutral-950 px-4 text-sm font-semibold text-white transition hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {{ verifying ? 'Verifying...' : 'Try verification again' }}
        </button>
      </form>

      <div class="flex flex-col gap-3 sm:flex-row">
        <NuxtLink
          to="/login"
          class="inline-flex h-11 flex-1 items-center justify-center rounded-md bg-neutral-950 px-4 text-sm font-semibold text-white transition hover:bg-neutral-800"
        >
          Sign in
        </NuxtLink>
        <NuxtLink
          to="/support"
          class="inline-flex h-11 flex-1 items-center justify-center rounded-md border border-neutral-300 px-4 text-sm font-semibold text-neutral-800 transition hover:border-neutral-950"
        >
          Support
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { definePageMeta, useRoute } from '#imports'
import { useApiFetch } from '~/composables/api'
import { toUserFriendlyErrorMessage } from '~/composables/userFacingError'

const CONFIRM_EMAIL_PATH = '/user/auth/confirm-email'

definePageMeta({
  layout: 'login',
  requiresAuth: false,
  head: {
    title: 'Verify your email - Jarvis',
    meta: [{ name: 'robots', content: 'noindex' }]
  }
})

const route = useRoute()
const state = ref<'verifying' | 'success' | 'error'>('verifying')
const verifying = ref(false)
const errorMessage = ref('')
const manualToken = ref('')

const heading = computed(() => {
  if (state.value === 'success') return 'Email verified'
  if (state.value === 'error') return 'Verification failed'
  return 'Verifying your email'
})

const message = computed(() => {
  if (state.value === 'success') return 'Your Jarvis account is ready. Sign in to continue.'
  if (state.value === 'error') return errorMessage.value || 'The verification link is invalid or expired.'
  return 'This usually only takes a moment.'
})

function extractToken(value: string | null | undefined): string {
  if (!value) return ''
  try {
    const url = new URL(value)
    return url.searchParams.get('token') || value
  } catch {
    return value
  }
}

async function verifyToken(rawToken: string) {
  const token = extractToken(rawToken)
  if (!token) {
    state.value = 'error'
    errorMessage.value = 'Missing verification token.'
    return
  }

  verifying.value = true
  const { error } = await useApiFetch('POST', CONFIRM_EMAIL_PATH, { token })
  verifying.value = false

  if (error) {
    state.value = 'error'
    errorMessage.value = toUserFriendlyErrorMessage(error)
    return
  }

  state.value = 'success'
}

async function manuallyVerify() {
  await verifyToken(manualToken.value)
}

onMounted(() => {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  void verifyToken(token)
})
</script>
