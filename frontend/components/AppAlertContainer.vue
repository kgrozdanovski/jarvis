<template>
  <div
      class="alert-container absolute top-0 mt-3 min-h-[4rem] h-fit-content
        left-1/2 transform -translate-x-1/2 ml-32
        text-center flex flex-col-reverse justify-center align-center gap-2 w-fit-content"
  >
    <AppAlert
        v-for="(alert, index) in state.alerts"
        :key="index"
        :type="alert.type"
        :message="alert.message"
        @closeAlert="closeAlert(index)"
    ></AppAlert>
  </div>
</template>

<style scoped>
.alert-container {
  z-index: 3000;
}
</style>

<script setup lang="ts">
import AppAlert from "~/components/AppAlert.vue";
import { useAlert } from '@/composables/alert';

const { state } = useAlert();
</script>

<script lang="ts">
export default {
  methods: {
    closeAlert(index: number) {
      // todo: make this smarter, the following approach is flawed
      // state.alerts.splice(index, 1);
    }
  }
}
</script>
