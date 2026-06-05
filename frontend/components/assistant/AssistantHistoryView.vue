<template>
  <section class="assistant-history-grid assistant-fade">
    <article v-for="group in history" :key="group.group" class="assistant-card assistant-history-col">
      <header>
        <strong>{{ group.group }}</strong>
        <span class="assistant-data">{{ group.count }}</span>
      </header>

      <button
        v-for="item in group.items"
        :key="`${group.group}-${item.time}-${item.q}`"
        type="button"
        class="assistant-history-item"
        :class="{ accented: item.acc }"
        @click="$emit('replay', item.q)"
      >
        <span class="assistant-data">{{ item.time }}</span>
        <span>
          <strong>{{ item.q }}</strong>
          <span class="assistant-tag-list">
            <span class="assistant-type-tag">{{ item.type }}</span>
            <span v-for="tag in item.tags" :key="`${item.q}-${tag}`" class="assistant-small-tag">
              {{ tag }}
            </span>
          </span>
        </span>
      </button>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { AssistantHistoryGroup } from '~/composables/useAssistantConsole'

defineProps<{
  history: AssistantHistoryGroup[]
}>()

defineEmits<{
  replay: [query: string]
}>()
</script>
