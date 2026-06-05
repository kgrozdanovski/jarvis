<template>
  <svg
    aria-hidden="true"
    class="assistant-mark"
    viewBox="0 0 100 100"
    :width="size"
    :height="size"
  >
    <defs>
      <linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#3B6CFF" />
        <stop offset="1" stop-color="#9B5CFF" />
      </linearGradient>
    </defs>
    <path
      d="M 50 22 L 81 73 L 19 73 Z"
      :fill="outline ? 'none' : fill"
      :stroke="fill"
      :stroke-width="outline ? 7 : 16"
      stroke-linejoin="round"
      stroke-linecap="round"
    />
  </svg>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance } from 'vue'

const props = withDefaults(
  defineProps<{
    size?: number
    mono?: boolean
    outline?: boolean
  }>(),
  {
    size: 28,
    mono: false,
    outline: false
  }
)

const instance = getCurrentInstance()
const gradientId = `jarvis-mark-gradient-${instance?.uid ?? 'static'}`
const fill = computed(() => (props.mono ? 'currentColor' : `url(#${gradientId})`))
</script>
