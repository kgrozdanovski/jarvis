# Jarvis Frontend

Nuxt 3 web app for the Jarvis local-network home AI assistant.

## Directory Structure

```bash
public/       Static assets.
assets/       Shared CSS and frontend assets.
components/   Vue components.
composables/  Vue composables.
layouts/      Nuxt layouts.
pages/        Nuxt routes.
plugins/      Client/server plugins.
store/        Pinia stores.
```

## Runtime Environment

Use Nuxt runtime config for API and browser-facing values:

- `HTTP_API_URL`: Backend HTTP base URL.
- `WS_API_URL`: Backend websocket host if realtime features are enabled.
- `NUXT_PUBLIC_ASSISTANT_API_ENABLED`: Set to `true` to have the assistant console call the placeholder
  `/assistant/*` endpoints. Leave unset for the local mock snapshot used while the backend is incomplete.
- `GOOGLE_OAUTH_CLIENT_ID` or `NUXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`: Optional Google sign-in client id.
- `GOOGLE_TAG_ID` or `NUXT_PUBLIC_GOOGLE_TAG_ID`: Optional GA4 tracking id.
- `NUXT_CLARITY_ID`: Optional Microsoft Clarity project id.

This Jarvis baseline only documents environment values used by the active local assistant frontend.
