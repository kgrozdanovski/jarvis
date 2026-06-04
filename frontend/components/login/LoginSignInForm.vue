<template>
  <form @submit.prevent="$emit('submit')" class="space-y-4">
    <div class="mb-2">
      <label class="block text-sm font-medium text-neutral-800 mb-1">Email</label>
      <div class="w-full h-11 md:h-12 px-4 flex items-center rounded-xl border border-neutral-200 bg-neutral-50 text-neutral-700">
        {{ form.email }}
        <button type="button" @click="$emit('change-email')" class="ml-auto text-sm underline underline-offset-2 hover:text-neutral-900">
          Change
        </button>
      </div>
    </div>

    <div>
      <div class="flex items-center justify-between mb-1">
        <label for="password" class="block text-sm font-medium text-neutral-800">Password</label>
        <button type="button" class="text-sm text-neutral-700 hover:text-neutral-900 underline-offset-2 hover:underline" @click="$emit('forgot')">
          Forgot?
        </button>
      </div>

      <div class="relative">
        <input
          id="password"
          :type="showPassword ? 'text' : 'password'"
          v-model="form.password"
          required
          autocomplete="current-password"
          placeholder="••••••••"
          class="input-base pr-16 autofill-fix rounded-xl border border-neutral-200
                 focus:border-neutral-600 focus:outline-none focus:ring-0 transition-colors"
        />
        <button
          type="button"
          @click="$emit('toggle-password')"
          :aria-label="showPassword ? 'Hide password' : 'Show password'"
          class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-zinc-400 hover:text-zinc-600"
        >
          <template v-if="!showPassword">
            <!-- eye-off -->
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M2 2L22 22" stroke="#000000" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="M6.713 6.723C3.665 8.795 2 12 2 12s3.636 7 10 7c2.05 0 3.817-.727 5.271-1.712M11 5.058C11.325 5.02 11.659 5 12 5c6.364 0 10 7 10 7s-.692 1.332-2 2.834" stroke="#000000" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round"></path>
              <path d="M14 14.236c-.531.475-1.232.764-2 .764A3 3 0 1 1 12 9c-.824 0-1.57.332-2.131.888" stroke="#000000" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
          </template>
          <template v-else>
            <!-- eye -->
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"/>
              <circle cx="12" cy="12" r="3" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"/>
            </svg>
          </template>
        </button>
      </div>
    </div>

    <div class="flex items-center justify-between">
      <label class="inline-flex items-center gap-2 text-sm text-neutral-700">
        <input type="checkbox" v-model="form.remember" class="accent-jarvisred-600 rounded" />
        Remember me
      </label>
    </div>

    <p v-if="error" class="text-sm text-jarvisred-600">{{ error }}</p>

    <button
      type="submit"
      :disabled="loading || !form.password"
      class="w-full h-12 mt-2 luxury-red-gradient !shadow-none text-white rounded-full text-lg font-medium transition-all duration-300 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <span v-if="!loading">Sign in</span>
      <span v-else>Signing in…</span>
    </button>

    <!-- magic link CTA -->
    <button
      type="button"
      @click="$emit('send-magic-link')"
      :disabled="magicLinkLoading"
      class="w-full h-11 md:h-12 mt-3 border border-neutral-300 rounded-full hover:border-neutral-900 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <span v-if="!magicLinkLoading">Email me a magic link</span>
      <span v-else>Sending…</span>
    </button>
  </form>
</template>

<script setup lang="ts">
defineProps<{
  form: { email: string; password: string; remember: boolean }
  showPassword: boolean
  loading: boolean
  error: string
  magicLinkLoading: boolean
}>()

defineEmits<{
  (e: 'submit'): void
  (e: 'change-email'): void
  (e: 'forgot'): void
  (e: 'toggle-password'): void
  (e: 'send-magic-link'): void
}>()
</script>
