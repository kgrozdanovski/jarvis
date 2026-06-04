import * as Sentry from "@sentry/nuxt";

Sentry.init({
  dsn: "https://b0d61cf7b0bd4e335245b88755dd8fed@o4511122784780289.ingest.de.sentry.io/4511125200109648",
  tracesSampleRate: 0.1,
  enableLogs: true,
  sendDefaultPii: false,
  environment: process.env.NODE_ENV ?? "production",
  debug: false,
});
