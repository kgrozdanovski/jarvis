<template>
  <div class="w-full" id="google-signin-container">
    <button
      type="button"
      :disabled="!ready || loading || confirmingLink"
      @click="handleClick"
      class="w-full h-11 md:h-12 flex items-center justify-center gap-3 border border-neutral-300 hover:border-neutral-900
             text-neutral-800 hover:text-neutral-900 rounded-full px-5 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
    >
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512" class="w-5 h-5" fill="currentColor" aria-hidden="true">
        <path d="M488 261.8C488 403.3 391.1 504 248.9 504 111.3 504 0 392.7 0 255.1 0 117.5 111.3 6.2 248.9 6.2c66.9 0 123 24.6 166.4 64.9l-67.5 64.9C319.6 108.3 287.2 96 248.9 96 164 96 94.7 165.4 94.7 250.3c0 84.9 69.4 154.3 154.3 154.3 98.6 0 135.6-70.8 141.3-107.6H248.9v-86.3H480c4 20.4 8 40.7 8 51.1z"/>
      </svg>

      <span class="font-medium pl-2">
        <template v-if="!loading && !confirmingLink">Continue with Google</template>
        <template v-else-if="confirmingLink">Linking…</template>
        <template v-else>Connecting…</template>
      </span>
    </button>

    <p v-if="error" class="mt-2 text-sm text-jarvisred-600 text-center">{{ error }}</p>

    <div
      v-if="linkPrompt"
      class="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
    >
      <p class="font-medium">Already have an account?</p>
      <p class="mt-1">
        We found an existing Jarvis account for <span class="font-semibold">{{ linkPrompt.email }}</span>.
        Connect it to Google so you can keep using both sign-in methods.
      </p>
      <div class="mt-3 flex flex-col gap-2 sm:flex-row">
        <button
          type="button"
          class="flex-1 rounded-full bg-neutral-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          :disabled="confirmingLink"
          @click="confirmLinking"
        >
          Yes, connect accounts
        </button>
        <button
          type="button"
          class="flex-1 rounded-full border border-neutral-300 px-4 py-2 text-sm font-semibold text-neutral-800"
          :disabled="confirmingLink"
          @click="cancelLinking"
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRoute, useRouter } from "#imports"
import { useAuth } from "~/composables/auth"
import { toUserFriendlyErrorMessage } from "~/composables/userFacingError"

type LinkPrompt = {
  token: string
  email: string
  existingName?: string | null
  googleName?: string | null
}

const { handleSuccessfulLogin } = useAuth()
const { $loadGis } = useNuxtApp() as any

const runtime = useRuntimeConfig()
const apiBase = runtime.public.apiBase
const clientId = runtime.public.googleClientId || runtime.public.GOOGLE_OAUTH_CLIENT_ID

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const confirmingLink = ref(false)
const error = ref<string | null>(null)
const ready = ref(false)
const linkPrompt = ref<LinkPrompt | null>(null)

let googleId: any = null

const completeLogin = async (loginPayload: any) => {
  if (!loginPayload?.access_token) {
    throw new Error("Invalid Google login response")
  }
  await handleSuccessfulLogin(loginPayload)
  const next =
    typeof route.query.next === "string" && route.query.next.startsWith("/")
      ? route.query.next
      : "/account"
  await router.replace(next)
}

const handleCredential = async (resp: any) => {
  if (!resp?.credential) return
  try {
    loading.value = true
    error.value = null

    const result: any = await $fetch(`${apiBase}/auth/google/login`, {
      method: "POST",
      credentials: "include",
      body: { credential: resp.credential },
    })

    if (result?.status === "link_required") {
      linkPrompt.value = {
        token: result.link_token,
        email: result.email,
        existingName: result.existing_name,
        googleName: result.google_name,
      }
      return
    }

    await completeLogin(result?.login ?? result)
  } catch (e: any) {
    error.value = toUserFriendlyErrorMessage()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await $loadGis()
  const google = (window as any).google
  googleId = google?.accounts?.id
  if (!googleId || !clientId) {
    // error.value = "Google Sign-In is not configured."
    return
  }

  googleId.initialize({
    client_id: clientId,
    callback: handleCredential,
    auto_select: false,
    cancel_on_tap_outside: true,
    use_fedcm_for_prompt: true,
  })
  ready.value = true
})

function handleClick() {
  if (!ready.value || loading.value || confirmingLink.value) return
  if (!googleId) {
    error.value = "Google Sign-In is unavailable."
    return
  }
  linkPrompt.value = null
  error.value = null
  googleId.prompt((notification: any) => {
    if (notification.isDismissedMoment?.()) {
      const reason = notification.getDismissedReason?.()
      if (reason && reason !== "credential_returned" && reason !== "cancel_called") {
        error.value = "Google Sign-In was dismissed. Please try again."
      }
    }
  })
}

async function confirmLinking() {
  if (!linkPrompt.value) return
  try {
    confirmingLink.value = true
    error.value = null
    const login = await $fetch(`${apiBase}/auth/google/link`, {
      method: "POST",
      credentials: "include",
      body: { token: linkPrompt.value.token },
    })
    await completeLogin(login)
  } catch (e: any) {
    error.value = toUserFriendlyErrorMessage()
  } finally {
    confirmingLink.value = false
    linkPrompt.value = null
  }
}

function cancelLinking() {
  linkPrompt.value = null
  confirmingLink.value = false
}
</script>
