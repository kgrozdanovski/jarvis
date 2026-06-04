<template>
  <div class="min-h-screen bg-neutral-50 text-neutral-950">
    <section class="mx-auto grid min-h-screen max-w-6xl content-center gap-12 px-4 pb-20 pt-32 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
      <div>
        <p class="text-sm font-semibold uppercase tracking-widest text-neutral-500">Local AI assistant</p>
        <h1 class="mt-4 text-5xl font-bold leading-tight tracking-tight sm:text-6xl">Jarvis for your home network</h1>
        <p class="mt-6 max-w-2xl text-lg leading-8 text-neutral-600">
          A private assistant interface for coordinating home automations, local AI tools, and household knowledge without payment or ecommerce workflows.
        </p>
        <div class="mt-8 flex flex-col gap-3 sm:flex-row">
          <NuxtLink to="/login" class="inline-flex items-center justify-center rounded-md bg-neutral-950 px-5 py-3 text-sm font-semibold text-white hover:bg-neutral-800">
            Sign in
          </NuxtLink>
          <NuxtLink to="/support" class="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white px-5 py-3 text-sm font-semibold text-neutral-900 hover:bg-neutral-100">
            Contact support
          </NuxtLink>
        </div>
      </div>

      <div id="assistant" class="rounded-lg border border-neutral-200 bg-white p-5 shadow-sm">
        <div class="border-b border-neutral-200 pb-4">
          <p class="text-sm font-semibold text-neutral-900">Assistant Console</p>
          <p class="mt-1 text-sm text-neutral-500">Ready on local network</p>
        </div>
        <div class="space-y-4 py-5">
          <div class="rounded-md bg-neutral-100 p-4">
            <p class="text-sm font-medium text-neutral-900">Morning status</p>
            <p class="mt-1 text-sm text-neutral-600">Lights, weather, calendar, and reminders in one place.</p>
          </div>
          <div class="rounded-md bg-neutral-100 p-4">
            <p class="text-sm font-medium text-neutral-900">Private tools</p>
            <p class="mt-1 text-sm text-neutral-600">Designed for local services and authenticated household access.</p>
          </div>
        </div>
        <div id="network" class="rounded-md border border-neutral-200 p-4">
          <p class="text-sm font-semibold text-neutral-900">Local-first baseline</p>
          <p class="mt-1 text-sm text-neutral-600">The app is focused on private home-assistant accounts and local-network access.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Jarvis | Local Home AI Assistant',
  meta: [
    {
      name: 'description',
      content: 'Jarvis is a local-network home AI assistant interface.'
    }
  ]
})
</script>
