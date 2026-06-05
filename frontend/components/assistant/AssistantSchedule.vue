<template>
  <section class="assistant-calendar assistant-fade">
    <article class="assistant-card assistant-schedule-card">
      <header class="assistant-card-head">
        <span>
          <span class="assistant-eyebrow">Today</span>
          <strong>{{ todayLabel }}</strong>
        </span>
        <AssistantBadge kind="accent">{{ events.length }} events</AssistantBadge>
      </header>

      <div class="assistant-timeline">
        <span v-if="showNowLine" class="assistant-nowline" :style="{ top: `${nowPct}%` }" />
        <div v-for="hour in hours" :key="hour" class="assistant-timeline-row">
          <span class="assistant-data">{{ formatHour(hour) }}</span>
          <div>
            <article
              v-for="event in events.filter((item) => item.h === hour)"
              :key="`${event.h}-${event.label}`"
              class="assistant-event"
              :class="event.tone"
            >
              <strong>{{ event.label }}</strong>
              <small class="assistant-data">{{ event.meta }}</small>
            </article>
          </div>
        </div>
      </div>
    </article>

    <aside class="assistant-side-list">
      <article class="assistant-card solid assistant-next-card">
        <span class="assistant-eyebrow">Up next</span>
        <template v-if="nextEvent">
          <strong class="assistant-next-time assistant-data">{{ formatHour(nextEvent.h) }}</strong>
          <span>{{ nextEvent.label }}</span>
          <small class="assistant-data">{{ nextEvent.meta }}</small>
        </template>
        <span v-else>Nothing left today.</span>
      </article>

      <article class="assistant-card solid assistant-summary-list">
        <span class="assistant-eyebrow">At a glance</span>
        <div v-for="item in summary" :key="item.title" class="assistant-summary-row">
          <span class="assistant-device-icon">
            <AssistantIcon :name="item.icon" :size="18" />
          </span>
          <span>
            <strong>{{ item.title }}</strong>
            <small class="assistant-data">{{ item.sub }}</small>
          </span>
        </div>
      </article>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AssistantCalendarEvent } from '~/composables/useAssistantConsole'
import AssistantBadge from './AssistantBadge.vue'
import AssistantIcon from './AssistantIcon.vue'

const props = defineProps<{
  events: AssistantCalendarEvent[]
  now: Date
}>()

const startH = 8
const endH = 20
const hours = Array.from({ length: endH - startH + 1 }, (_, index) => startH + index)

const todayLabel = computed(() => props.now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short' }))
const currentMinutes = computed(() => props.now.getHours() * 60 + props.now.getMinutes())
const totalMinutes = (endH - startH) * 60
const nowPct = computed(() => Math.max(0, Math.min(100, ((currentMinutes.value - startH * 60) / totalMinutes) * 100)))
const showNowLine = computed(() => props.now.getHours() >= startH && props.now.getHours() <= endH)
const nextEvent = computed(() => props.events.find((event) => event.h * 60 >= currentMinutes.value))
const summary = [
  { icon: 'users', title: '3 meetings', sub: '2h 30m total' },
  { icon: 'rocket', title: '1 deploy window', sub: '15:00 - prod-eu' },
  { icon: 'coffee', title: '2 personal', sub: 'lunch + dinner' }
]

const formatHour = (hour: number) => `${String(hour).padStart(2, '0')}:00`
</script>
