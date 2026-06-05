<template>
  <div class="assistant-palette-backdrop" @click.self="$emit('close')">
    <section class="assistant-palette" role="dialog" aria-modal="true" aria-label="Jarvis command palette">
      <label class="assistant-palette-input">
        <AssistantIcon name="search" :size="20" />
        <input
          ref="inputRef"
          v-model="query"
          type="search"
          placeholder="Ask, run a command, or simulate an event"
          @keydown="handleKey"
        />
      </label>

      <div class="assistant-palette-list">
        <p v-if="visibleItems.length === 0" class="assistant-palette-empty">No matches</p>
        <template v-for="(entry, index) in visibleItems" :key="`${entry.section}-${entry.label}`">
          <div v-if="shouldShowSection(index)" class="assistant-palette-section">
            {{ entry.section }}
          </div>
          <button
            type="button"
            class="assistant-palette-item"
            :class="{ selected: index === selectedIndex }"
            @mouseenter="selectedIndex = index"
            @click="run(entry.command)"
          >
            <AssistantIcon :name="entry.icon" :size="18" />
            <span>{{ entry.label }}</span>
            <small v-if="entry.meta" class="assistant-data">{{ entry.meta }}</small>
          </button>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import AssistantIcon from './AssistantIcon.vue'

const props = defineProps<{
  theme: 'dark' | 'light'
}>()

const emit = defineEmits<{
  close: []
  run: [command: string]
  toggleTheme: []
}>()

interface PaletteEntry {
  section: string
  icon: string
  label: string
  command: string
  meta?: string
}

const inputRef = ref<HTMLInputElement | null>(null)
const query = ref('')
const selectedIndex = ref(0)

const entries = computed<PaletteEntry[]>(() => [
  { section: 'Ask Jarvis', icon: 'radio', label: 'Show the home network', command: 'Show me the home network' },
  { section: 'Ask Jarvis', icon: 'calendar-days', label: "Open today's schedule", command: "What's on my calendar today?" },
  { section: 'Ask Jarvis', icon: 'images', label: 'Porto trip photos', command: 'Photos from the Porto trip' },
  { section: 'Ask Jarvis', icon: 'sparkles', label: "How's the deploy looking?", command: "How's the prod deploy looking?" },
  { section: 'Simulate event', icon: 'video', label: 'Front door motion detected', command: '__event:door', meta: 'Event' },
  { section: 'Simulate event', icon: 'git-branch', label: 'Deploy window starting', command: '__event:deploy', meta: 'Event' },
  { section: 'Simulate event', icon: 'sunrise', label: 'Deliver morning brief', command: '__event:brief', meta: 'Event' },
  { section: 'Workspace', icon: 'brain', label: 'Open Memory', command: '__panel:memory' },
  { section: 'Workspace', icon: 'history', label: 'Open History', command: '__panel:history' },
  { section: 'Workspace', icon: props.theme === 'dark' ? 'sun' : 'moon', label: `Switch to ${props.theme === 'dark' ? 'light' : 'dark'} theme`, command: '__theme' },
  { section: 'Workspace', icon: 'home', label: 'Return to idle', command: '__idle' }
])

const visibleItems = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return entries.value
  return entries.value.filter((entry) => entry.label.toLowerCase().includes(q))
})

const shouldShowSection = (index: number) => {
  const current = visibleItems.value[index]
  const previous = visibleItems.value[index - 1]
  return current && current.section !== previous?.section
}

const run = (command: string) => {
  if (command === '__theme') {
    emit('toggleTheme')
    emit('close')
    return
  }
  emit('run', command)
}

const handleKey = (event: KeyboardEvent) => {
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    selectedIndex.value = Math.min(selectedIndex.value + 1, visibleItems.value.length - 1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
  } else if (event.key === 'Enter') {
    event.preventDefault()
    const selected = visibleItems.value[selectedIndex.value]
    if (selected) run(selected.command)
  } else if (event.key === 'Escape') {
    emit('close')
  }
}

watch(query, () => {
  selectedIndex.value = 0
})

onMounted(async () => {
  await nextTick()
  inputRef.value?.focus()
})
</script>
