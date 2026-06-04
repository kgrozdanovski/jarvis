<template>
  <section class="mx-auto max-w-5xl px-4 py-12 sm:px-6">
    <div class="mb-8">
      <p class="text-sm font-semibold uppercase tracking-widest text-neutral-500">Jarvis</p>
      <h1 class="mt-3 text-4xl font-bold tracking-tight text-neutral-950">Account</h1>
      <p class="mt-3 max-w-2xl text-neutral-600">
        Manage the local assistant account used to access Jarvis on your home network.
      </p>
    </div>

    <div class="grid gap-6 lg:grid-cols-[1fr_0.75fr]">
      <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-neutral-950">Profile</h2>
            <p class="mt-1 text-sm text-neutral-500">Keep your display name up to date.</p>
          </div>
          <span
            class="rounded-full border px-3 py-1 text-xs font-semibold"
            :class="isVerified ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'"
          >
            {{ isVerified ? 'Verified' : 'Unverified' }}
          </span>
        </div>

        <form class="mt-6 space-y-4" @submit.prevent="saveProfile">
          <div>
            <label class="block text-sm font-medium text-neutral-700" for="name">Name</label>
            <input
              id="name"
              v-model="fullName"
              class="mt-2 w-full rounded-md border border-neutral-300 px-3 py-2 text-neutral-950 outline-none focus:border-neutral-900"
              type="text"
              autocomplete="name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-neutral-700" for="email">Email</label>
            <input
              id="email"
              :value="userEmail"
              class="mt-2 w-full rounded-md border border-neutral-200 bg-neutral-100 px-3 py-2 text-neutral-600"
              type="email"
              disabled
            />
          </div>
          <button
            class="rounded-md bg-neutral-950 px-4 py-2 text-sm font-semibold text-white hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            :disabled="loadingProfile || !fullName.trim()"
          >
            {{ loadingProfile ? 'Saving...' : 'Save profile' }}
          </button>
        </form>
      </div>

      <div class="space-y-6">
        <div class="rounded-lg border border-neutral-200 bg-white p-6 shadow-sm">
          <h2 class="text-xl font-semibold text-neutral-950">Access</h2>
          <dl class="mt-4 space-y-3 text-sm">
            <div class="flex justify-between gap-4">
              <dt class="text-neutral-500">Mode</dt>
              <dd class="font-medium text-neutral-950">Local</dd>
            </div>
            <div class="flex justify-between gap-4">
              <dt class="text-neutral-500">Created</dt>
              <dd class="font-medium text-neutral-950">{{ registrationDate || 'Loading...' }}</dd>
            </div>
          </dl>
          <NuxtLink
            to="/account/change-password"
            class="mt-5 inline-flex rounded-md border border-neutral-300 px-4 py-2 text-sm font-semibold text-neutral-900 hover:bg-neutral-50"
          >
            Change password
          </NuxtLink>
        </div>

        <div class="rounded-lg border border-red-200 bg-white p-6 shadow-sm">
          <h2 class="text-xl font-semibold text-neutral-950">Delete account</h2>
          <p class="mt-2 text-sm text-neutral-600">
            Request a confirmation email before permanently deleting this account.
          </p>
          <button
            class="mt-5 rounded-md border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
            type="button"
            :disabled="deleteLoading"
            @click="requestDeletion"
          >
            {{ deleteLoading ? 'Sending...' : 'Send deletion email' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAlert } from '~/composables/alert'
import { useAuthStore } from '~/store/auth'

definePageMeta({
  layout: 'authenticated',
  requiresAuth: true
})

const authStore = useAuthStore()
const { addAlert } = useAlert()

const loadingProfile = ref(false)
const deleteLoading = ref(false)
const fullName = ref('')
const userEmail = ref('')
const isVerified = ref(false)
const createdAt = ref<string | null>(null)

const registrationDate = computed(() => {
  if (!createdAt.value) return ''
  const date = new Date(createdAt.value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
})

const syncAuthProfile = (payload: any) => {
  const current = authStore.getCurrentUser()
  authStore.setUser({
    name: payload.name ?? current?.name ?? '',
    email: payload.email ?? current?.email ?? '',
    public_id: payload.public_id ?? current?.public_id ?? '',
    tier: 'local'
  })
}

const loadProfile = async () => {
  loadingProfile.value = true
  try {
    const { data, error } = await useApiFetch('GET', '/user/me')
    if (error || !data) throw error || new Error('No profile returned')
    const profile = data as any
    fullName.value = profile.name || ''
    userEmail.value = profile.email || ''
    isVerified.value = Boolean(profile.is_verified)
    createdAt.value = profile.created_at || null
    syncAuthProfile(profile)
  } catch (error) {
    addAlert('Failed to load account profile.', 'error')
  } finally {
    loadingProfile.value = false
  }
}

const saveProfile = async () => {
  const trimmed = fullName.value.trim()
  if (!trimmed) return
  loadingProfile.value = true
  try {
    const { data, error } = await useApiFetch('PATCH', '/user/profile', { name: trimmed })
    if (error || !data) throw error || new Error('No profile returned')
    const profile = data as any
    fullName.value = profile.name || trimmed
    syncAuthProfile(profile)
    addAlert('Profile updated.', 'success')
  } catch (error) {
    addAlert('Failed to update profile.', 'error')
  } finally {
    loadingProfile.value = false
  }
}

const requestDeletion = async () => {
  deleteLoading.value = true
  try {
    const { error } = await useApiFetch('POST', '/user/account/delete-request')
    if (error) throw error
    addAlert('Deletion confirmation email sent.', 'success')
  } catch (error) {
    addAlert('Failed to send deletion confirmation.', 'error')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(loadProfile)
</script>
