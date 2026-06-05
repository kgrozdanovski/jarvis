<template>
  <div class="assistant-console" :data-theme="theme">
    <div class="assistant-watermark">
      <AssistantMark :size="520" outline />
    </div>

    <nav class="assistant-rail" aria-label="Jarvis workspace">
      <button type="button" class="assistant-mark-button" title="Jarvis" @click="goIdle">
        <AssistantMark :size="34" />
      </button>
      <button
        type="button"
        class="assistant-nav-button"
        :class="{ active: mode === 'idle' }"
        title="Home"
        @click="goIdle"
      >
        <AssistantIcon name="home" />
      </button>
      <button
        type="button"
        class="assistant-nav-button"
        :class="{ active: response?.type === 'memory' }"
        title="Memory"
        @click="openView('memory')"
      >
        <AssistantIcon name="brain" />
      </button>
      <button
        type="button"
        class="assistant-nav-button"
        :class="{ active: response?.type === 'history' }"
        title="History"
        @click="openView('history')"
      >
        <AssistantIcon name="history" />
      </button>
      <div class="assistant-rail-spacer" />
      <button type="button" class="assistant-nav-button" title="Theme" @click="toggleTheme">
        <AssistantIcon :name="theme === 'dark' ? 'sun' : 'moon'" />
      </button>
    </nav>

    <section class="assistant-main">
      <header class="assistant-topbar">
        <div class="assistant-brand">
          <strong>Jarvis</strong>
          <span>
            <i class="assistant-status-dot" />
            {{ statusLabel }}
          </span>
        </div>

        <div class="assistant-source-list-top">
          <span
            v-for="source in snapshot.sources"
            :key="source.id"
            class="assistant-source-pill"
            :class="{ active: activeSource === source.id }"
          >
            <AssistantIcon :name="source.icon" :size="14" />
            {{ source.label }}
          </span>
        </div>

        <label class="assistant-model-select">
          <AssistantIcon name="server" :size="16" />
          <select v-model="selectedModel">
            <option value="fast_model">fast_model</option>
            <option value="smart_model">smart_model</option>
            <option value="local_model">local_model</option>
          </select>
        </label>

        <button type="button" class="assistant-search-button" title="Command palette" @click="paletteOpen = true">
          <AssistantIcon name="search" :size="17" />
          <span>Ask or command</span>
        </button>
      </header>

      <div class="assistant-canvas-wrap">
        <div class="assistant-canvas">
          <AssistantIdle
            v-if="mode === 'idle'"
            :now="now"
            :suggestions="snapshot.suggestions"
            :calendar-events="snapshot.calendarEvents"
            :device-count="onlineDeviceCount"
            @suggest="submit"
          />

          <AssistantThinking v-else-if="mode === 'thinking'" />

          <template v-else-if="mode === 'answer' && response">
            <template v-if="response.type === 'memory' || response.type === 'history'">
              <header class="assistant-view-head">
                <span class="assistant-view-icon">
                  <AssistantIcon :name="response.type === 'memory' ? 'brain' : 'history'" :size="26" />
                </span>
                <span>
                  <span class="assistant-eyebrow">
                    {{ response.type === 'memory' ? 'On-device context' : 'One continuous thread' }}
                  </span>
                  <strong>{{ response.type === 'memory' ? 'Memory' : 'History' }}</strong>
                </span>
                <button type="button" class="assistant-icon-button" title="Close" @click="goIdle">
                  <AssistantIcon name="x" :size="18" />
                </button>
              </header>

              <AssistantMemoryView v-if="response.type === 'memory'" :memory="snapshot.memory" />
              <AssistantHistoryView v-else :history="snapshot.history" @replay="submit" />
            </template>

            <template v-else>
              <header class="assistant-query-head">
                <span class="assistant-query-avatar">
                  <AssistantIcon :name="activeSourceIcon" :size="18" />
                </span>
                <span class="assistant-query-copy">
                  <span class="assistant-query-meta">
                    <span class="assistant-eyebrow">{{ activeSourceLabel }} - just now</span>
                    <AssistantBadge kind="accent">{{ responseTypeLabel }}</AssistantBadge>
                  </span>
                  <strong>{{ query }}</strong>
                </span>
                <button type="button" class="assistant-icon-button" title="Back to idle" @click="goIdle">
                  <AssistantIcon name="rotate-ccw" :size="18" />
                </button>
              </header>

              <AssistantTextAnswer v-if="response.type === 'text'" :query="response.query" />
              <AssistantGallery v-else-if="response.type === 'gallery'" :gallery="snapshot.gallery" />
              <AssistantDeviceMap
                v-else-if="response.type === 'devicemap'"
                :devices="snapshot.devices"
                :focus="response.focus"
              />
              <AssistantSchedule
                v-else-if="response.type === 'calendar'"
                :events="snapshot.calendarEvents"
                :now="now"
              />
            </template>
          </template>
        </div>
      </div>

      <footer class="assistant-dock">
        <Transition name="assistant-soft">
          <div v-if="toast" class="assistant-event-toast">
            <span class="assistant-event-icon">
              <AssistantIcon :name="toast.icon" :size="16" />
            </span>
            <span><strong>{{ toast.toast.lead }}</strong> - {{ toast.toast.sub }}</span>
          </div>
        </Transition>

        <form class="assistant-dockbar" :class="{ listening }" @submit.prevent="submit(inputText)">
          <AssistantMark :size="26" />
          <div v-if="listening" class="assistant-wave" aria-label="Listening">
            <i
              v-for="bar in waveBars"
              :key="bar.index"
              :style="{ animationDelay: bar.delay, height: bar.height }"
            />
          </div>
          <input
            v-else
            v-model="inputText"
            type="text"
            placeholder="Ask Jarvis anything"
            autocomplete="off"
          />
          <button
            type="button"
            class="assistant-dock-button"
            :class="{ active: listening }"
            title="Voice"
            @click="toggleMic"
          >
            <AssistantIcon :name="listening ? 'square' : 'mic'" :size="19" />
          </button>
          <button type="submit" class="assistant-dock-button send" title="Send">
            <AssistantIcon name="arrow-up" :size="19" />
          </button>
        </form>

        <div class="assistant-runtime-row">
          <span>
            <AssistantIcon :name="backendEnabled ? 'plug-zap' : 'lock'" :size="14" />
            {{ backendEnabled ? 'Backend endpoints enabled' : 'Local mock snapshot' }}
          </span>
          <span>
            <AssistantIcon name="sliders-horizontal" :size="14" />
            {{ selectedModel }}
          </span>
        </div>
      </footer>
    </section>

    <AssistantCommandPalette
      v-if="paletteOpen"
      :theme="theme"
      @close="paletteOpen = false"
      @run="runCommand"
      @toggle-theme="toggleTheme"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  assistantSnapshot,
  type AssistantEvent,
  type AssistantResponse,
  type AssistantResponseType,
  type AssistantSnapshot,
  type AssistantSourceId,
  useAssistantConsoleApi
} from '~/composables/useAssistantConsole'
import AssistantBadge from './AssistantBadge.vue'
import AssistantCommandPalette from './AssistantCommandPalette.vue'
import AssistantDeviceMap from './AssistantDeviceMap.vue'
import AssistantGallery from './AssistantGallery.vue'
import AssistantHistoryView from './AssistantHistoryView.vue'
import AssistantIcon from './AssistantIcon.vue'
import AssistantIdle from './AssistantIdle.vue'
import AssistantMark from './AssistantMark.vue'
import AssistantMemoryView from './AssistantMemoryView.vue'
import AssistantSchedule from './AssistantSchedule.vue'
import AssistantTextAnswer from './AssistantTextAnswer.vue'
import AssistantThinking from './AssistantThinking.vue'

type AssistantMode = 'idle' | 'thinking' | 'answer'
type AssistantTheme = 'dark' | 'light'

const api = useAssistantConsoleApi()
const snapshot = ref<AssistantSnapshot>(assistantSnapshot)
const mode = ref<AssistantMode>('idle')
const response = ref<AssistantResponse | null>(null)
const query = ref('')
const inputText = ref('')
const paletteOpen = ref(false)
const listening = ref(false)
const now = ref(new Date())
const activeSource = ref<AssistantSourceId>('screen')
const toast = ref<AssistantEvent | null>(null)
const theme = ref<AssistantTheme>('dark')
const selectedModel = ref('fast_model')

const voiceSamples = [
  'Show me the home network',
  "What's on my calendar today?",
  'Photos from the Porto trip'
]
const waveBars = Array.from({ length: 34 }, (_, index) => ({
  index,
  delay: `${index * 0.045}s`,
  height: `${8 + Math.abs(Math.sin(index * 0.9)) * 18}px`
}))

let clockTimer: ReturnType<typeof setInterval> | null = null
let voiceTimer: ReturnType<typeof setTimeout> | null = null
let toastTimer: ReturnType<typeof setTimeout> | null = null
let idleTimer: ReturnType<typeof setTimeout> | null = null
let interactionId = 0
let firedAutoEvent = false

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const onlineDeviceCount = computed(() => snapshot.value.devices.filter((device) => device.status !== 'off').length)
const backendEnabled = computed(() => api.backendEnabled.value)
const statusLabel = computed(() => {
  if (mode.value === 'thinking') return 'Working'
  if (mode.value === 'answer') return 'Active'
  return 'Listening - idle'
})
const activeSourceMeta = computed(() => snapshot.value.sources.find((source) => source.id === activeSource.value))
const activeSourceIcon = computed(() => activeSourceMeta.value?.icon ?? 'monitor')
const activeSourceLabel = computed(() => activeSourceMeta.value?.label ?? 'You')
const responseTypeLabel = computed(() => {
  const labels: Record<AssistantResponseType, string> = {
    text: 'Answer',
    gallery: 'Gallery',
    devicemap: 'Network map',
    calendar: 'Schedule',
    memory: 'Memory',
    history: 'History'
  }
  return response.value ? labels[response.value.type] : 'Answer'
})

const setTheme = (nextTheme: AssistantTheme) => {
  theme.value = nextTheme
  if (import.meta.client) {
    localStorage.setItem('jarvis-theme', nextTheme)
  }
}

const toggleTheme = () => {
  setTheme(theme.value === 'dark' ? 'light' : 'dark')
}

const goIdle = () => {
  mode.value = 'idle'
  response.value = null
  query.value = ''
  paletteOpen.value = false
}

const openView = (view: 'memory' | 'history') => {
  listening.value = false
  paletteOpen.value = false
  activeSource.value = 'screen'
  query.value = view === 'memory' ? 'Memory' : 'History'
  response.value = { type: view, query: query.value }
  mode.value = 'answer'
}

const submit = async (raw: string, source: AssistantSourceId = 'screen') => {
  const trimmed = raw.trim()
  if (!trimmed) return

  const currentInteraction = ++interactionId
  inputText.value = ''
  listening.value = false
  paletteOpen.value = false
  activeSource.value = source
  query.value = trimmed
  response.value = null
  mode.value = 'thinking'

  const [nextResponse] = await Promise.all([
    api.sendMessage(trimmed, source, { model: selectedModel.value }),
    wait(api.backendEnabled.value ? 450 : 1150)
  ])

  if (currentInteraction !== interactionId) return
  response.value = nextResponse
  mode.value = 'answer'
}

const eventResponse = (event: AssistantEvent): AssistantResponse => {
  if (event.respond === 'door-motion') {
    return { type: 'devicemap', query: event.toast.lead, focus: 'door' }
  }
  if (event.respond === 'deploy') {
    return { type: 'text', query: "How's the prod-eu deploy looking?" }
  }
  return { type: 'calendar', query: event.toast.lead }
}

const fireEvent = async (eventId: string) => {
  const event = await api.triggerEvent(eventId)
  if (!event) return

  const currentInteraction = ++interactionId
  paletteOpen.value = false
  activeSource.value = 'screen'
  toast.value = event
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value = null
  }, 5200)

  query.value = event.toast.lead
  response.value = null
  mode.value = 'thinking'
  await wait(950)
  if (currentInteraction !== interactionId) return
  response.value = eventResponse(event)
  mode.value = 'answer'
}

const runCommand = (command: string) => {
  if (command.startsWith('__event:')) {
    void fireEvent(command.slice('__event:'.length))
    return
  }
  if (command === '__panel:memory') {
    openView('memory')
    return
  }
  if (command === '__panel:history') {
    openView('history')
    return
  }
  if (command === '__idle') {
    goIdle()
    return
  }
  void submit(command, 'screen')
}

const toggleMic = () => {
  if (listening.value) {
    listening.value = false
    if (voiceTimer) clearTimeout(voiceTimer)
    return
  }

  listening.value = true
  const sample = voiceSamples[Math.floor(Math.random() * voiceSamples.length)]
  voiceTimer = setTimeout(() => {
    if (listening.value) {
      void submit(sample, 'screen')
    }
  }, 2200)
}

const handleKeyboard = (event: KeyboardEvent) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    paletteOpen.value = !paletteOpen.value
  } else if (event.key === 'Escape') {
    paletteOpen.value = false
  }
}

onMounted(async () => {
  const storedTheme = localStorage.getItem('jarvis-theme')
  if (storedTheme === 'dark' || storedTheme === 'light') {
    theme.value = storedTheme
  }

  snapshot.value = await api.loadSnapshot()
  clockTimer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  window.addEventListener('keydown', handleKeyboard)

  idleTimer = setTimeout(() => {
    if (!firedAutoEvent && mode.value === 'idle' && !paletteOpen.value) {
      firedAutoEvent = true
      void fireEvent('door')
    }
  }, 26000)
})

onBeforeUnmount(() => {
  if (clockTimer) clearInterval(clockTimer)
  if (voiceTimer) clearTimeout(voiceTimer)
  if (toastTimer) clearTimeout(toastTimer)
  if (idleTimer) clearTimeout(idleTimer)
  if (import.meta.client) {
    window.removeEventListener('keydown', handleKeyboard)
  }
})
</script>
