<template>
  <header class="fixed inset-x-0 top-0 z-50 border-b border-neutral-200 bg-white/90 backdrop-blur">
    <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
      <NuxtLink to="/admin/users" class="flex items-center gap-3" aria-label="Jarvis admin">
        <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-neutral-900 text-sm font-bold text-white">J</span>
        <span class="text-lg font-semibold text-neutral-950">Jarvis Admin</span>
      </NuxtLink>
      <div class="flex items-center gap-4">
        <NuxtLink to="/admin/users" class="text-sm text-neutral-600 hover:text-neutral-950">Users</NuxtLink>
        <NuxtLink to="/account" class="text-sm text-neutral-600 hover:text-neutral-950">Account</NuxtLink>
        <button class="rounded-md border border-neutral-300 px-3 py-2 text-sm font-semibold" type="button" @click="logout">
          Log out
        </button>
      </div>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from '#imports'
import { useAuthStore } from '~/store/auth'

const router = useRouter()

const logout = async () => {
  const authStore = useAuthStore()
  try {
    await useApiFetch('POST', '/user/auth/logout')
  } catch (_e) {}
  authStore.logout()
  await router.replace('/login')
}
</script>
