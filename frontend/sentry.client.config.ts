import * as Sentry from "@sentry/nuxt";

Sentry.init({
  // If set up, you can use your runtime config here
  // dsn: useRuntimeConfig().public.sentry.dsn,
  dsn: "https://b0d61cf7b0bd4e335245b88755dd8fed@o4511122784780289.ingest.de.sentry.io/4511125200109648",

  // We recommend adjusting this value in production, or using tracesSampler
  // for finer control
  tracesSampleRate: 0.1,
  enableLogs: true,
  // PII disabled by default; sentry-consent plugin enables it after "Accept All".
  sendDefaultPii: false,
  environment: import.meta.env.MODE ?? "production",
  debug: false,
});
