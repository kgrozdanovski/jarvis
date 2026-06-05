<template>
  <div class="assistant-ring" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg :width="size" :height="size" viewBox="0 0 100 100">
      <defs>
        <linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" :stop-color="color1" />
          <stop offset="1" :stop-color="color2" />
        </linearGradient>
      </defs>
      <circle class="assistant-ring-track" cx="50" cy="50" :r="radius" fill="none" :stroke-width="stroke" />
      <circle
        class="assistant-ring-value"
        cx="50"
        cy="50"
        :r="radius"
        fill="none"
        :stroke-width="stroke"
        :stroke="`url(#${gradientId})`"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
      />
    </svg>
    <div class="assistant-ring-label">
      <span class="assistant-data">{{ label }}</span>
      <span v-if="sub" class="assistant-eyebrow">{{ sub }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance } from 'vue'

const props = withDefaults(
  defineProps<{
    value?: number
    size?: number
    stroke?: number
    color1?: string
    color2?: string
    label: string
    sub?: string
  }>(),
  {
    value: 70,
    size: 84,
    stroke: 8,
    color1: '#3B6CFF',
    color2: '#9B5CFF',
    sub: ''
  }
)

const radius = computed(() => 50 - props.stroke / 2 - 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const offset = computed(() => circumference.value * (1 - props.value / 100))
const instance = getCurrentInstance()
const gradientId = `jarvis-ring-gradient-${instance?.uid ?? 'static'}`
</script>
