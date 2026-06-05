<template>
  <AssistantConsole />
</template>

<script setup lang="ts">
import AssistantConsole from '~/components/assistant/AssistantConsole.vue'

definePageMeta({
  layout: 'assistant'
})

useHead({
  title: 'Jarvis | Assistant Console',
  meta: [
    {
      name: 'description',
      content: 'Jarvis is a local-first assistant console for memory, events, devices, schedule, and voice workflows.'
    }
  ]
})
</script>
