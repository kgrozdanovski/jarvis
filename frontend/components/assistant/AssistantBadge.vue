<template>
  <span class="assistant-badge" :class="kind">
    <slot />
  </span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    kind?: 'ok' | 'warn' | 'danger' | 'accent' | 'neutral'
  }>(),
  {
    kind: 'neutral'
  }
)
</script>
