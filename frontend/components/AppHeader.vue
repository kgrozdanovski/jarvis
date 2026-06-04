<template>
  <header class="fixed inset-x-0 top-0 z-50 border-b border-neutral-200 bg-white/90 backdrop-blur">
    <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
      <NuxtLink to="/" class="flex items-center gap-3" aria-label="Jarvis home">
        <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-neutral-900 text-sm font-bold text-white">J</span>
        <span class="text-lg font-semibold text-neutral-950">Jarvis</span>
      </NuxtLink>

      <div class="hidden items-center gap-6 md:flex">
        <NuxtLink to="/#assistant" class="text-sm text-neutral-600 hover:text-neutral-950">Assistant</NuxtLink>
        <NuxtLink to="/#network" class="text-sm text-neutral-600 hover:text-neutral-950">Local Network</NuxtLink>
        <NuxtLink to="/support" class="text-sm text-neutral-600 hover:text-neutral-950">Support</NuxtLink>
      </div>

      <NuxtLink
        to="/login"
        class="inline-flex items-center rounded-md bg-neutral-950 px-4 py-2 text-sm font-semibold text-white hover:bg-neutral-800"
      >
        Sign in
      </NuxtLink>
    </nav>
  </header>
</template>
