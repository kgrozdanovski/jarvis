<template>
  <section class="grid min-h-screen bg-neutral-100 px-4 py-10 sm:px-6">
    <div class="m-auto w-full max-w-md rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
      <NuxtLink to="/" class="mb-8 flex items-center gap-3" aria-label="Jarvis home">
        <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-neutral-900 text-sm font-bold text-white">J</span>
        <span class="text-lg font-semibold text-neutral-950">Jarvis</span>
      </NuxtLink>

      <div class="mb-6">
        <h1 class="text-2xl font-bold text-neutral-950">{{ mode === 'login' ? 'Sign in' : 'Create account' }}</h1>
        <p class="mt-2 text-sm text-neutral-600">
          Access your local-network home assistant.
        </p>
      </div>

      <div class="mb-6 grid grid-cols-2 rounded-md bg-neutral-100 p-1">
        <button
          class="rounded px-3 py-2 text-sm font-semibold"
          :class="mode === 'login' ? 'bg-white text-neutral-950 shadow-sm' : 'text-neutral-600'"
          type="button"
          @click="mode = 'login'"
        >
          Sign in
        </button>
        <button
          class="rounded px-3 py-2 text-sm font-semibold"
          :class="mode === 'register' ? 'bg-white text-neutral-950 shadow-sm' : 'text-neutral-600'"
          type="button"
          @click="mode = 'register'"
        >
          Register
        </button>
      </div>

      <form class="space-y-4" @submit.prevent="mode === 'login' ? login() : register()">
        <div v-if="mode === 'register'">
          <label class="block text-sm font-medium text-neutral-700" for="name">Name</label>
          <input
            id="name"
            v-model="name"
            class="mt-2 w-full rounded-md border border-neutral-300 px-3 py-2 outline-none focus:border-neutral-900"
            type="text"
            autocomplete="name"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-neutral-700" for="email">Email</label>
          <input
            id="email"
            v-model="email"
            class="mt-2 w-full rounded-md border border-neutral-300 px-3 py-2 outline-none focus:border-neutral-900"
            type="email"
            autocomplete="email"
            required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-neutral-700" for="password">Password</label>
          <input
            id="password"
            v-model="password"
            class="mt-2 w-full rounded-md border border-neutral-300 px-3 py-2 outline-none focus:border-neutral-900"
            type="password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            required
            minlength="8"
          />
        </div>

        <p v-if="message" class="rounded-md bg-neutral-100 px-3 py-2 text-sm text-neutral-700">{{ message }}</p>
        <p v-if="error" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>

        <button
          class="w-full rounded-md bg-neutral-950 px-4 py-3 text-sm font-semibold text-white hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          :disabled="loading"
        >
          {{ loading ? 'Working...' : mode === 'login' ? 'Sign in' : 'Create account' }}
        </button>
      </form>

      <button
        class="mt-4 w-full text-sm font-medium text-neutral-600 hover:text-neutral-950"
        type="button"
        @click="sendReset"
      >
        Email me a reset link
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from '#imports'
import { useAuthStore } from '~/store/auth'

definePageMeta({ layout: 'login', requiresAuth: false })

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const name = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const message = ref('')

const nextPath = computed(() => {
  const raw = typeof route.query.next === 'string' ? route.query.next : '/account'
  return raw.startsWith('/') ? raw : '/account'
})

const login = async () => {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    const { data, error: requestError } = await useApiFetch('POST', '/user/auth/login', {
      email: email.value,
      password: password.value
    })
    if (requestError || !data) throw requestError || new Error('Login failed')
    const payload = data as any
    authStore.saveAuth(
      {
        id: payload.public_id,
        email: payload.email,
        name: payload.name,
        isAuthenticated: true,
        tier: 'local'
      },
      {
        accessToken: payload.access_token,
        accessTokenExpiresAt: payload.access_token_expires_at
      }
    )
    await router.replace(nextPath.value)
  } catch (_err) {
    error.value = 'Unable to sign in. Check your email, password, and verification status.'
  } finally {
    loading.value = false
  }
}

const register = async () => {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    const { error: requestError } = await useApiFetch('POST', '/user/auth/register', {
      name: name.value,
      email: email.value,
      password: password.value,
      next: '/account'
    })
    if (requestError) throw requestError
    message.value = 'Account created. Check your email to verify before signing in.'
    mode.value = 'login'
    password.value = ''
  } catch (_err) {
    error.value = 'Unable to create account. The email may already be registered.'
  } finally {
    loading.value = false
  }
}

const sendReset = async () => {
  error.value = ''
  message.value = ''
  if (!email.value) {
    error.value = 'Enter your email first.'
    return
  }
  const { error: requestError } = await useApiFetch('POST', '/user/auth/magic-link', { email: email.value })
  if (requestError) {
    error.value = 'Unable to send reset link right now.'
    return
  }
  message.value = 'If that account exists, a reset link has been sent.'
}
</script>
