<template>
  <div class="min-h-screen flex items-center justify-center bg-neutral-50 px-4">
    <div class="bg-white shadow-2xl rounded-3xl max-w-md w-full p-8 space-y-4 border border-neutral-200">
      <div class="flex items-center justify-center w-14 h-14 rounded-full bg-red-50 border border-red-100 mx-auto">
        <svg v-if="state === 'success'" class="w-8 h-8 text-emerald-500" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
        </svg>
        <svg v-else-if="state === 'verifying'" class="w-8 h-8 text-neutral-400 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <svg v-else class="w-8 h-8 text-red-500" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-4a1 1 0 112 0 1 1 0 01-2 0zm0-6a1 1 0 012 0v3a1 1 0 11-2 0V8z" clip-rule="evenodd"/>
        </svg>
      </div>

      <div class="text-center space-y-2">
        <h1 class="text-2xl font-bold text-neutral-900">
          <span v-if="state === 'success'">Account deleted</span>
          <span v-else-if="state === 'verifying'">Deleting your account…</span>
          <span v-else>Invalid or expired link</span>
        </h1>
        <p class="text-neutral-600" v-if="state === 'success'">
          Your account has been removed. You can always create a new account later.
        </p>
        <p class="text-neutral-600" v-else-if="state === 'verifying'">
          This only takes a moment.
        </p>
        <p class="text-neutral-600" v-else>
          The deletion link may have expired. You can request a new one from the account page.
        </p>
      </div>

      <div class="pt-2 text-center">
        <NuxtLink to="/login" class="inline-flex items-center justify-center px-5 py-3 rounded-full bg-neutral-900 text-white font-semibold hover:bg-neutral-800 transition">
          Back to sign in
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from '#imports'
import { definePageMeta } from '#imports'
import { useApiFetch } from '~/composables/api'

definePageMeta({ layout: 'login' })

const route = useRoute()
const state = ref<'verifying' | 'success' | 'error'>('verifying')

const confirmDeletion = async () => {
  const token = typeof route.query.token === 'string' ? route.query.token : null
  if (!token) {
    state.value = 'error'
    return
  }
  const { error } = await useApiFetch('POST', '/user/account/confirm-delete', { token })
  state.value = error ? 'error' : 'success'
}

onMounted(confirmDeletion)
</script>
