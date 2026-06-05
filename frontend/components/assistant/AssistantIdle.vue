<template>
  <section class="assistant-idle assistant-fade">
    <div class="assistant-idle-mark">
      <AssistantMark :size="96" />
    </div>
    <div class="assistant-clock assistant-data">
      {{ time }}
      <span>{{ seconds }}</span>
    </div>
    <div class="assistant-eyebrow">{{ date }}</div>
    <p class="assistant-greeting">
      {{ greeting }}, <strong>Alex.</strong> Everything is calm.
    </p>

    <div class="assistant-glance-grid">
      <article v-for="item in glances" :key="item.label" class="assistant-glance">
        <span class="assistant-glance-icon">
          <AssistantIcon :name="item.icon" :size="22" />
        </span>
        <span>
          <span class="assistant-eyebrow">{{ item.label }}</span>
          <strong class="assistant-data">{{ item.value }}</strong>
        </span>
      </article>
    </div>

    <div class="assistant-suggestions">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion.label"
        type="button"
        class="assistant-chip"
        @click="$emit('suggest', suggestion.label)"
      >
        <AssistantIcon :name="suggestion.icon" :size="16" />
        <span>{{ suggestion.label }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AssistantCalendarEvent, AssistantSuggestion } from '~/composables/useAssistantConsole'
import AssistantIcon from './AssistantIcon.vue'
import AssistantMark from './AssistantMark.vue'

const props = defineProps<{
  now: Date
  suggestions: AssistantSuggestion[]
  calendarEvents: AssistantCalendarEvent[]
  deviceCount: number
}>()

defineEmits<{
  suggest: [query: string]
}>()

const time = computed(() => props.now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }))
const seconds = computed(() => props.now.toLocaleTimeString('en-GB', { second: '2-digit' }))
const date = computed(() => props.now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' }))
const greeting = computed(() => {
  const hour = props.now.getHours()
  if (hour < 5) return 'Resting'
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
})

const nextEvent = computed(() => props.calendarEvents.find((event) => event.h >= props.now.getHours()) ?? props.calendarEvents[0])

const glances = computed(() => [
  { icon: 'cloud-sun', label: 'Lisbon', value: '22 C' },
  { icon: 'calendar-clock', label: 'Next up', value: nextEvent.value?.label ?? 'Clear' },
  { icon: 'package', label: 'Parcel', value: 'ETA 14:20' },
  { icon: 'activity', label: 'Systems', value: `${props.deviceCount} online` }
])
</script>
