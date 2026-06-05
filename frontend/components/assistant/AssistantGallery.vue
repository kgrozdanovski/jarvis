<template>
  <section class="assistant-gallery assistant-fade">
    <div class="assistant-gallery-grid">
      <article
        v-for="item in gallery"
        :key="item.cap"
        class="assistant-gallery-tile"
        :style="{ background: item.gradient }"
      >
        <span v-if="item.tag" class="assistant-gallery-tag">{{ item.tag }}</span>
        <div class="assistant-gallery-caption">
          <strong>{{ item.cap }}</strong>
          <span>{{ item.sub }}</span>
        </div>
      </article>
    </div>
    <div class="assistant-inline-meta">
      <AssistantBadge kind="accent">{{ gallery.length }} images</AssistantBadge>
      <span>Porto scouting - phone sync</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AssistantGalleryItem } from '~/composables/useAssistantConsole'
import AssistantBadge from './AssistantBadge.vue'

defineProps<{
  gallery: AssistantGalleryItem[]
}>()
</script>
