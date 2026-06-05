<template>
  <section class="assistant-netmap assistant-fade">
    <div class="assistant-netcanvas">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <line
          v-for="device in edgeDevices"
          :key="device.id"
          :x1="hub?.x"
          :y1="hub?.y"
          :x2="device.x"
          :y2="device.y"
          :class="{ selected: device.id === selectedId, warning: device.status === 'warn' }"
          vector-effect="non-scaling-stroke"
        />
      </svg>

      <button
        v-for="device in devices"
        :key="device.id"
        type="button"
        class="assistant-node"
        :class="{ hub: device.hub, selected: device.id === selectedId, offline: device.status === 'off' }"
        :style="{ left: `${device.x}%`, top: `${device.y}%` }"
        @click="selectedId = device.id"
      >
        <span class="assistant-node-dot">
          <AssistantIcon :name="device.icon" :size="device.hub ? 30 : 22" />
          <span v-if="!device.hub" class="assistant-node-status" :class="device.status" />
        </span>
        <span class="assistant-node-label">{{ device.name }}</span>
      </button>
    </div>

    <aside class="assistant-side-list">
      <article class="assistant-card solid assistant-selected-device">
        <span class="assistant-eyebrow">Selected</span>
        <div class="assistant-selected-row">
          <span class="assistant-device-icon">
            <AssistantIcon :name="selectedDevice?.icon" :size="22" />
          </span>
          <span>
            <strong>{{ selectedDevice?.name }}</strong>
            <small class="assistant-data">{{ selectedDevice?.meta }}</small>
          </span>
        </div>
        <div class="assistant-badge-row">
          <AssistantBadge :kind="selectedDevice?.status === 'warn' ? 'warn' : 'ok'">
            {{ selectedDevice?.status === 'warn' ? 'Streaming' : 'Online' }}
          </AssistantBadge>
          <AssistantBadge>{{ selectedDevice?.hub ? 'Gateway' : 'Edge' }}</AssistantBadge>
        </div>
      </article>

      <button
        v-for="device in edgeDevices"
        :key="device.id"
        type="button"
        class="assistant-device-row"
        :class="{ selected: device.id === selectedId }"
        @click="selectedId = device.id"
      >
        <span class="assistant-device-icon">
          <AssistantIcon :name="device.icon" :size="18" />
        </span>
        <span>
          <strong>{{ device.name }}</strong>
          <small class="assistant-data">{{ device.meta }}</small>
        </span>
        <span class="assistant-node-status inline" :class="device.status" />
      </button>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { AssistantDevice } from '~/composables/useAssistantConsole'
import AssistantBadge from './AssistantBadge.vue'
import AssistantIcon from './AssistantIcon.vue'

const props = defineProps<{
  devices: AssistantDevice[]
  focus?: string
}>()

const selectedId = ref(props.focus || 'router')

const hub = computed(() => props.devices.find((device) => device.hub))
const edgeDevices = computed(() => props.devices.filter((device) => !device.hub))
const selectedDevice = computed(() => props.devices.find((device) => device.id === selectedId.value) ?? hub.value)

watch(
  () => props.focus,
  (focus) => {
    if (focus) selectedId.value = focus
  }
)
</script>
