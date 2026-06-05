<template>
  <section class="assistant-memory-view assistant-fade">
    <article class="assistant-card assistant-memory-summary">
      <AssistantRing label="9" sub="items" :value="72" :size="72" />
      <span>
        <strong>9 memories - 3 active rules</strong>
        <p>
          Local memory placeholders are shaped for the future backend journal and graph store.
        </p>
      </span>
    </article>

    <section v-for="group in memory" :key="group.group" class="assistant-memory-group">
      <span class="assistant-eyebrow">{{ group.group }}</span>
      <div class="assistant-memory-grid">
        <article v-for="item in group.items" :key="`${group.group}-${item.title}`" class="assistant-card assistant-memory-card">
          <span class="assistant-device-icon">
            <AssistantIcon :name="item.icon" :size="19" />
          </span>
          <strong>{{ item.title }}</strong>
          <p>{{ item.body }}</p>
          <small class="assistant-data">{{ item.meta }}</small>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import type { AssistantMemoryGroup } from '~/composables/useAssistantConsole'
import AssistantIcon from './AssistantIcon.vue'
import AssistantRing from './AssistantRing.vue'

defineProps<{
  memory: AssistantMemoryGroup[]
}>()
</script>
