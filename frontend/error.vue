<template>
  <div class="flex min-h-screen flex-col items-center justify-center bg-neutral-100 px-4 py-16 text-center">
    <NuxtLink to="/" class="mb-8 flex items-center gap-3" aria-label="Jarvis home">
      <span class="flex h-10 w-10 items-center justify-center rounded-lg bg-neutral-900 text-sm font-bold text-white">J</span>
      <span class="text-lg font-semibold text-neutral-950">Jarvis</span>
    </NuxtLink>

    <div class="w-full max-w-md rounded-lg border border-neutral-200 bg-white p-8 shadow-sm">
      <p class="text-sm font-semibold uppercase tracking-widest text-neutral-500">
        {{ error?.statusCode ?? 404 }}
      </p>
      <h1 class="mt-3 text-3xl font-bold text-neutral-950">Page not found</h1>
      <p class="mt-3 text-neutral-600">The page does not exist or has been removed.</p>
      <NuxtLink
        to="/"
        class="mt-8 inline-flex rounded-md bg-neutral-950 px-5 py-3 text-sm font-semibold text-white hover:bg-neutral-800"
      >
        Back to Jarvis
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useError } from '#imports'

const error = useError()
</script>
