<template>
  <div
      class="app-alert p-2 items-center leading-none lg:rounded-full flex lg:inline-flex
        transition-all duration-500 w-fit-content h-fit-content"
      :class="[alertClass, { 'opacity-0': !isVisible}]"
      role="alert"
  >
    <span
        class="flex rounded-full uppercase px-2 py-1 text-xs !font-bold mr-3"
        :class="badgeClass"
    >{{ type }}</span>
    <span class="text-sm mr-2 text-left flex-auto">{{ message }}</span>
    <X
        class="fill-current opacity-75 h-4 w-4 hover:cursor-pointer"
        :stroke-width="1"
        @click="closeAlert()"
    />
  </div>
</template>

<style scoped>
.app-alert.hover svg,
.app-alert:hover svg {
  stroke-width: 3; /* increase the stroke width as needed */
}
</style>

<script setup lang="ts">
import {X} from 'lucide-vue-next'
</script>

<script lang="ts">
export default {
  props: {
    message: {
      type: String,
      default: '',
    },
    type: {
      type: String,
      default: 'info',
    },
  },
  data() {
    return {
      isVisible: true
    }
  },
  mounted() {
    // Change opacity to 0 after 3 seconds
    setTimeout(() => {
      this.isVisible = false;
    }, 3000)
  },
  methods: {
    closeAlert() {
      this.isVisible = false
      this.$emit('closeAlert')
    }
  },
  computed: {
    alertClass(): String {
      switch (this.type) {
        case 'error':
          return 'dark:bg-red-400 dark:text-red-950 bg-red-200 text-red-800'
        case 'warning':
          return 'dark:bg-yellow-400 dark:text-yellow-900 bg-yellow-200 text-yellow-800'
        case 'info':
          return 'dark:bg-sky-400 dark:text-sky-900 bg-sky-200 text-sky-800'
        case 'success':
          return 'dark:bg-emerald-400 dark:text-emerald-900 bg-emerald-200 text-emerald-800'
        case 'neutral':
        default:
          return 'dark:bg-neutral-400 dark:text-neutral-900 bg-neutral-200 text-neutral-800'
      }
    },
    badgeClass(): String {
      switch (this.type) {
        case 'error':
          return 'dark:bg-red-600 dark:text-red-200 bg-red-500 text-red-100';
        case 'warning':
          return 'dark:bg-yellow-600 dark:text-yellow-200 bg-yellow-500 text-yellow-100';
        case 'info':
          return 'dark:bg-sky-600 dark:text-sky-200 bg-sky-500 text-sky-100';
        case 'success':
          return 'dark:bg-emerald-600 dark:text-emerald-100 bg-emerald-500 text-emerald-100'
        case 'neutral':
        default:
          return 'dark:bg-neutral-600 dark:text-neutral-200 bg-neutral-500 text-neutral-100';
      }
    },
  }
}
</script>
