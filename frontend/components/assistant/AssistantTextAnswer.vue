<template>
  <section class="assistant-text-answer assistant-fade">
    <p class="assistant-answer-lead">
      {{ visibleLead }}<span v-if="!leadDone" class="assistant-cursor" />
    </p>

    <Transition name="assistant-soft">
      <div v-if="leadDone" class="assistant-answer-detail">
        <div class="assistant-answer-points">
          <article v-for="point in answer.points" :key="point.title" class="assistant-answer-point">
            <AssistantMark :size="13" />
            <div>
              <strong>{{ point.title }}</strong>
              <p>{{ point.body }}</p>
            </div>
          </article>
        </div>

        <div class="assistant-source-list">
          <button v-for="source in answer.sources" :key="source.title" type="button" class="assistant-source">
            <span class="assistant-source-avatar" :style="{ backgroundColor: source.color }">
              {{ source.initials }}
            </span>
            <span>
              <strong>{{ source.title }}</strong>
              <small>{{ source.url }}</small>
            </span>
          </button>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { pickAssistantTextAnswer } from '~/composables/useAssistantConsole'
import AssistantMark from './AssistantMark.vue'

const props = defineProps<{
  query: string
}>()

const answer = computed(() => pickAssistantTextAnswer(props.query))
const visibleLead = ref('')
const leadDone = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

const resetTypewriter = () => {
  if (timer) clearInterval(timer)
  visibleLead.value = ''
  leadDone.value = false

  let index = 0
  timer = setInterval(() => {
    const lead = answer.value.lead
    index += Math.max(1, Math.round(lead.length / 90))
    if (index >= lead.length) {
      visibleLead.value = lead
      leadDone.value = true
      if (timer) clearInterval(timer)
      timer = null
      return
    }
    visibleLead.value = lead.slice(0, index)
  }, 16)
}

watch(() => props.query, resetTypewriter, { immediate: true })

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>
