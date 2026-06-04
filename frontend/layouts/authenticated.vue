<template>
  <div class="min-h-screen bg-neutral-100 text-neutral-950">
    <AppAuthenticatedHeader />
    <AppAlertContainer />
    <AppAnnouncementDialog />
    <main class="min-h-screen pt-20">
      <NuxtPage />
    </main>
    <AppAuthenticatedFooter />
  </div>
</template>

<script setup lang="ts">
import AppAlertContainer from '~/components/AppAlertContainer.vue'
import AppAnnouncementDialog from '~/components/AppAnnouncementDialog.vue'
import AppAuthenticatedFooter from '~/components/layout/authenticated/AppAuthenticatedFooter.vue'
import AppAuthenticatedHeader from '~/components/layout/authenticated/AppAuthenticatedHeader.vue'
import { buildSoftwareLdJson, useDefaultSeo } from '~/utils/seo'

useDefaultSeo()
useHead({
  script: [
    {
      type: 'application/ld+json',
      children: JSON.stringify(buildSoftwareLdJson()),
      key: 'ld-software-jarvis'
    }
  ]
})
</script>
