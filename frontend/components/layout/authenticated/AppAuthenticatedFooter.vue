<template>
  <footer class="border-t border-neutral-200 bg-white">
    <div class="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 text-sm text-neutral-600 sm:px-6 md:flex-row md:items-center md:justify-between">
      <p>© {{ new Date().getFullYear() }} Jarvis.</p>
      <div class="flex flex-wrap gap-4">
        <NuxtLink to="/account" class="hover:text-neutral-950">Account</NuxtLink>
        <NuxtLink to="/support" class="hover:text-neutral-950">Support</NuxtLink>
        <NuxtLink to="/privacy-policy" class="hover:text-neutral-950">Privacy</NuxtLink>
      </div>
    </div>
  </footer>
</template>
