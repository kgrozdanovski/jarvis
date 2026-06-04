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
      <label for="name" class="block text-sm font-medium text-neutral-800 mb-1">Your name</label>
      <input
        id="name"
        v-model.trim="form.name"
        type="text"
        autocomplete="name"
        placeholder="Alex Stone"
        class="input-base rounded-xl border border-neutral-200 focus:border-neutral-600 focus:outline-none focus:ring-0 transition-colors"
        required
      />
    </div>

    <!-- Password with validation -->
    <div>
      <label for="new-password" class="block text-sm font-medium text-neutral-800 mb-1">Create password</label>
      <div class="relative">
        <input
          id="new-password"
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          placeholder="••••••••"
          class="input-base pr-16 autofill-fix rounded-xl border border-neutral-200 focus:border-neutral-600 focus:outline-none focus:ring-0 transition-colors"
          required
          minlength="8"
          @input="$emit('validate-password')"
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
              <path d="M2 2L22 22" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M6.7 6.72C3.66 8.8 2 12 2 12s3.64 7 10 7c2.05 0 3.82-.73 5.27-1.72M11 5.06c.33-.04.66-.06 1-.06 6.36 0 10 7 10 7s-.69 1.33-2 2.83" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 14.24A3 3 0 0 1 9 12c0-.82.33-1.57.87-2.11" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round"/>
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
      <p class="mt-1 text-xs text-neutral-600">Use at least 8 characters, with a number and a letter.</p>
      <p v-if="passwordMessage" :class="['text-xs mt-1', passwordValid ? 'text-emerald-600' : 'text-jarvisred-600']">
        {{ passwordMessage }}
      </p>
    </div>

    <!-- Confirm Password -->
    <div>
      <label for="confirm_password" class="block text-sm font-medium text-neutral-800 mb-1">Confirm password</label>
      <div class="relative">
        <input
          id="confirm_password"
          v-model="form.confirmPassword"
          :type="showConfirm ? 'text' : 'password'"
          autocomplete="new-password"
          placeholder="••••••••"
          class="input-base pr-16 autofill-fix rounded-xl border border-neutral-200 focus:border-neutral-600 focus:outline-none focus:ring-0 transition-colors"
          required
        />
        <button
          type="button"
          @click="$emit('toggle-confirm')"
          :aria-label="showConfirm ? 'Hide password' : 'Show password'"
          class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-zinc-400 hover:text-zinc-600"
        >
          <template v-if="!showConfirm">
            <!-- eye-off -->
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M2 2L22 22" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M6.7 6.72C3.66 8.8 2 12 2 12s3.64 7 10 7c2.05 0 3.82-.73 5.27-1.72M11 5.06c.33-.04.66-.06 1-.06 6.36 0 10 7 10 7s-.69 1.33-2 2.83" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 14.24A3 3 0 0 1 9 12c0-.82.33-1.57.87-2.11" stroke-width="1.344" stroke-linecap="round" stroke-linejoin="round"/>
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
      <p v-if="confirmMessage" :class="['text-xs mt-1', passwordsMatch ? 'text-emerald-600' : 'text-jarvisred-600']">
        {{ confirmMessage }}
      </p>
    </div>

    <label class="inline-flex items-center gap-2 text-sm text-neutral-700">
      <input type="checkbox" v-model="form.agree" class="accent-jarvisred-600 rounded" />
      I agree to the <NuxtLink to="/tos" target="_blank" rel="noopener noreferrer" class="underline underline-offset-2 hover:text-neutral-900">Terms</NuxtLink> and
      <NuxtLink to="/privacy-policy" target="_blank" rel="noopener noreferrer" class="underline underline-offset-2 hover:text-neutral-900">Privacy Policy</NuxtLink>.
    </label>

    <p v-if="error" class="text-sm text-jarvisred-600">{{ error }}</p>

    <button
      type="submit"
      :disabled="loading || !canSignUp"
      class="w-full h-12 mt-2 luxury-red-gradient !shadow-none text-white rounded-full text-lg font-medium transition-all duration-300 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <span v-if="!loading">Create account</span>
      <span v-else>Creating…</span>
    </button>
  </form>
</template>

<script setup lang="ts">
defineProps<{
  form: {
    email: string
    name: string
    password: string
    confirmPassword: string
    agree: boolean
  }
  showPassword: boolean
  showConfirm: boolean
  loading: boolean
  error: string
  canSignUp: boolean
  passwordMessage: string
  passwordValid: boolean
  confirmMessage: string
  passwordsMatch: boolean
}>()

defineEmits<{
  (e: 'submit'): void
  (e: 'change-email'): void
  (e: 'toggle-password'): void
  (e: 'toggle-confirm'): void
  (e: 'validate-password'): void
}>()
</script>
