<template>
  <section class="assistant-thinking assistant-fade" aria-live="polite">
    <div class="assistant-thinking-mark">
      <span class="assistant-thinking-orbit one"><AssistantMark :size="84" /></span>
      <span class="assistant-thinking-orbit two"><AssistantMark :size="118" /></span>
      <span class="assistant-thinking-orbit three"><AssistantMark :size="64" /></span>
      <span class="assistant-thinking-pane" />
    </div>
    <div class="assistant-thinking-status">
      <p>{{ activeStep.label }}</p>
      <div class="assistant-thinking-steps">
        <span
          v-for="(step, index) in steps"
          :key="step.label"
          class="assistant-step"
          :class="{ done: index < stepIndex, active: index === stepIndex }"
        >
          <AssistantIcon :name="index < stepIndex ? 'check' : step.icon" :size="14" />
          {{ step.label }}
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import AssistantIcon from './AssistantIcon.vue'
import AssistantMark from './AssistantMark.vue'

const steps = [
  { icon: 'scan-search', label: 'Parsing request' },
  { icon: 'database', label: 'Recalling context' },
  { icon: 'cpu', label: 'Reasoning' },
  { icon: 'layout-template', label: 'Composing view' }
]

const stepIndex = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const activeStep = computed(() => steps[stepIndex.value] ?? steps[0])

onMounted(() => {
  timer = setInterval(() => {
    stepIndex.value = Math.min(stepIndex.value + 1, steps.length - 1)
  }, 460)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>
