<template>
  <transition name="fade">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-end md:items-center justify-center px-0 md:px-4 py-0 md:py-6 bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      @click.self="closeModal"
    >
      <div class="relative w-full md:max-w-3xl bg-white md:rounded-2xl rounded-t-3xl shadow-2xl border border-neutral-200 overflow-hidden max-h-[92vh] md:max-h-[90vh] overflow-y-auto">
        <div class="grid grid-cols-1 md:grid-cols-5">
          <div class="md:col-span-2 p-5 md:p-7 bg-neutral-50 border-b md:border-b-0 md:border-r border-neutral-200">
            <p class="text-xs tracking-[0.12em] font-semibold text-neutral-500">NEWSLETTER</p>
            <h3 class="mt-2 text-xl md:text-2xl font-bold text-neutral-900 hero-text-gradient">Get Jarvis updates</h3>
            <p class="mt-2 text-neutral-600 text-sm md:text-base">
              Short notes about local assistant improvements and setup changes.
            </p>
            <ul class="mt-4 md:mt-6 space-y-2 md:space-y-3 text-neutral-700 text-sm md:text-base">
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-emerald-500 mr-1 md:mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                Local-network assistant features.
              </li>
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-emerald-500 mr-1 md:mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                Practical setup and account updates.
              </li>
              <li class="flex items-center gap-2">
                <svg class="w-4 h-4 md:w-5 md:h-5 text-emerald-500 mr-1 md:mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                No spam - just one concise email.
              </li>
            </ul>
          </div>

          <div class="md:col-span-3 p-5 md:p-7">
            <div class="flex justify-end mb-3 md:mb-4">
              <button
                type="button"
                class="p-2 rounded-full text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100"
                aria-label="Close"
                @click="closeModal"
              >
                <svg class="w-5 h-5" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>

            <div v-if="status === 'success'" class="space-y-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                  </svg>
                </div>
                <div>
                  <p class="text-base font-semibold text-neutral-900">{{ successMessage }}</p>
                  <p class="text-sm text-neutral-600">We will send the next update shortly.</p>
                </div>
              </div>
              <button
                type="button"
                class="inline-flex items-center justify-center px-6 py-3 rounded-full luxury-red-gradient !shadow-none text-white font-medium hover:shadow-lg transition-all"
                @click="closeModal"
              >
                Close
              </button>
            </div>

            <form v-else class="space-y-4" @submit.prevent="submit">
              <div class="grid grid-cols-1 gap-3">
                <div>
                  <label class="sr-only" for="newsletter-name">Name</label>
                  <input
                    id="newsletter-name"
                    v-model.trim="form.name"
                    type="text"
                    placeholder="Name (optional)"
                    autocomplete="name"
                    class="w-full px-4 py-3 border rounded-2xl md:rounded-lg border-neutral-200 focus:outline-none focus:ring-2 focus:ring-red-500 text-base"
                    :disabled="isLocked"
                  />
                </div>
                <div>
                  <label class="sr-only" for="newsletter-email">Email</label>
                  <input
                    id="newsletter-email"
                    v-model.trim="form.email"
                    type="email"
                    placeholder="Work email"
                    autocomplete="email"
                    class="w-full px-4 py-3 border rounded-2xl md:rounded-lg border-neutral-200 focus:outline-none focus:ring-2 focus:ring-red-500 text-base"
                    :aria-invalid="!!errors.email"
                    :disabled="isLocked"
                  />
                  <p v-if="errors.email" class="mt-1 text-sm text-red-600">{{ errors.email }}</p>
                </div>
                <label class="sr-only" for="newsletter-website">Website</label>
                <input
                  id="newsletter-website"
                  v-model="form.website"
                  type="text"
                  tabindex="-1"
                  autocomplete="off"
                  class="hidden"
                />
              </div>

              <div class="space-y-3">
                <div v-if="errorMessage" class="text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
                  {{ errorMessage }}
                </div>
                <button
                  type="submit"
                  class="w-full luxury-red-gradient !shadow-none text-white py-4 md:py-3 px-6 rounded-2xl md:rounded-full text-lg font-semibold md:font-medium transition-all duration-300 hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
                  :disabled="isLocked"
                >
                  <span v-if="status === 'sending'" class="flex items-center justify-center gap-2">
                    <span class="inline-block h-4 w-4 rounded-full border-2 border-white/60 border-t-white animate-spin"></span>
                    Joining…
                  </span>
                  <span v-else>Subscribe</span>
                </button>
                <p class="text-sm text-neutral-600 text-center">One concise email per week. Unsubscribe anytime.</p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useApiFetch } from '~/composables/api'
import { useAuthStore } from '~/store/auth'
import { toUserFriendlyErrorMessage } from '~/composables/userFacingError'

const props = defineProps({
  open: { type: Boolean, default: false },
  entrySource: { type: String, default: 'newsletter' },
  pageUrl: { type: String, default: '' }
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'subscribed'): void
}>()

const form = reactive({
  name: '',
  email: '',
  website: '',
  userId: '',
  userPlan: ''
})

const errors = reactive<Record<string, string>>({})
const status = ref<'idle' | 'sending' | 'success' | 'error'>('idle')
const errorMessage = ref('')
const successMessage = ref('Thanks for subscribing!')

const authStore = useAuthStore()
const currentUser = computed(() => (typeof authStore.getCurrentUser === 'function' ? authStore.getCurrentUser() : null))

const isOpen = computed({
  get: () => props.open,
  set: (val: boolean) => emit('update:open', val)
})

const isLocked = computed(() => status.value === 'sending')

const resetState = () => {
  Object.keys(errors).forEach((key) => delete errors[key])
  errorMessage.value = ''
  status.value = 'idle'
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      resetState()
      prefillFromUser()
    } else {
      form.name = ''
      form.email = ''
      form.website = ''
      form.userId = ''
      form.userPlan = ''
      status.value = 'idle'
    }
  }
)

watch(
  () => currentUser.value,
  () => {
    if (isOpen.value) {
      prefillFromUser()
    }
  }
)

const prefillFromUser = () => {
  const user = currentUser.value
  if (!user) return
  if (!form.email) form.email = user.email || ''
  if (!form.name) form.name = user.name || ''
  form.userId = String(user.id || '')
  form.userPlan = user.tier || ''
}

const validate = () => {
  Object.keys(errors).forEach((key) => delete errors[key])
  const emailPattern = /[^@\s]+@[^@\s]+\.[^@\s]+/
  if (!form.email || !emailPattern.test(form.email)) {
    errors.email = 'Enter a valid email address.'
  }
  return Object.keys(errors).length === 0
}

const submit = async () => {
  if (status.value === 'sending') return
  errorMessage.value = ''
  if (!validate()) return

  status.value = 'sending'
  const payload: Record<string, any> = {
    email: form.email,
    source: props.entrySource || 'newsletter',
    pageUrl: props.pageUrl || (import.meta.client ? window.location.href : undefined)
  }
  if (form.name) payload.name = form.name
  if (form.website) payload.website = form.website
  if (form.userId) payload.userId = form.userId
  if (form.userPlan) payload.userPlan = form.userPlan

  const { data, error } = await useApiFetch('POST', '/newsletter/subscribe', payload)
  if (error) {
    status.value = 'error'
    errorMessage.value = toUserFriendlyErrorMessage()
    return
  }

  status.value = 'success'
  successMessage.value = data?.message || 'Thanks for subscribing!'
  form.name = ''
  form.email = ''
  form.website = ''
  emit('subscribed')
}

const closeModal = () => {
  isOpen.value = false
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
