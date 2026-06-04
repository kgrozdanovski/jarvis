<template>
  <div class="transition-bg h-screen flex flex-col">
    <main class="light flex-grow flex flex-col bg-neutral-100 w-full">
      <AppAdminHeader />

      <AppAlertContainer />
      <AppAnnouncementDialog />

      <NuxtPage class="w-full" />

      <AppAuthenticatedFooter />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppAlertContainer from "~/components/AppAlertContainer.vue";
import AppAnnouncementDialog from "~/components/AppAnnouncementDialog.vue";
import AppAuthenticatedFooter from "~/components/layout/authenticated/AppAuthenticatedFooter.vue";
import AppAdminHeader from "~/components/layout/admin/AppAdminHeader.vue";
import { buildSoftwareLdJson, useDefaultSeo } from '~/utils/seo';

useDefaultSeo();
useHead({
  script: [
    {
      type: 'application/ld+json',
      children: JSON.stringify(buildSoftwareLdJson()),
      key: 'ld-software-jarvis'
    }
  ]
});
</script>

<style lang="scss">
body {
    background-color: #F6F6F6;
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* If this doesn't work, see `top: <scroll-margin-top>` property of ScrollBehavior in router.options.ts */
section {
  scroll-margin-top: 60px; /* adjust based on header height */
}

/*
 * Theme Overrides
 */
.v-theme--light {
  /* Must be comma-separated RGB values */
  --v-theme-surface: 250, 250, 250; /* tailwindcss zinc-50 */
  //--v-theme-surface: 244, 244, 245; /* tailwindcss zinc-200 */
}
.v-theme--dark {
  /* Must be comma-separated RGB values */
  //--v-theme-surface: 63, 63, 70; /* tailwindcss bg-neutral-700 */
  //--v-theme-surface: 39, 39, 42; /* tailwindcss bg-neutral-800 */
  --v-theme-surface: 24, 24, 27; /* tailwindcss bg-neutral-900 */
}

.transition-bg {
  transition: background-color 0.5s ease-in-out;
}
</style>
