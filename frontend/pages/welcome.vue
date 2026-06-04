<template>
  <section class="mx-auto max-w-4xl px-4 py-16 sm:px-6">
    <div class="rounded-lg border border-neutral-200 bg-white p-8 shadow-sm">
      <p class="text-sm font-semibold uppercase tracking-widest text-neutral-500">Account verified</p>
      <h1 class="mt-3 text-3xl font-bold text-neutral-950">Welcome to Jarvis</h1>
      <p class="mt-4 text-neutral-600">
        Your account is ready. Continue to the local assistant account area to manage your profile and access settings.
      </p>
      <NuxtLink
        to="/account"
        class="mt-6 inline-flex rounded-md bg-neutral-950 px-5 py-3 text-sm font-semibold text-white hover:bg-neutral-800"
      >
        Open account
      </NuxtLink>
    </div>
  </section>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'authenticated',
  requiresAuth: true
})
</script>
