# Frontend agent instructions (override)

Scope: `frontend/**`

## Do not run commands

This agent environment is sandboxed; do **not** run frontend commands to “check” work:
`npm …`, `pnpm …`, `yarn …`, `nuxt …`, `vite …`, etc. The user must run these locally.

## Project shape (Nuxt 3)

- Template: `frontend/design-template` must only be used as a reference design/layout for implementation, and is not
part of the project itself. It must also not be altered in any way.
- Config: `frontend/nuxt.config.ts` (modules, SSR, route rules, runtimeConfig, headers/caching).
- Pages and routing: `frontend/pages/`
- Components: `frontend/components/`
- Composables: `frontend/composables/`
- State: `frontend/store/` (Pinia)
- Styling: `frontend/assets/style/` + `frontend/tailwind.config.ts`

## Environment/runtime config rules

- Prefer `runtimeConfig.public` values (wired in `frontend/nuxt.config.ts`) over ad-hoc `process.env` access.
- Public env vars should use the `NUXT_PUBLIC_...` prefix where browser exposure is intentional.

## Style and conventions

- Keep changes consistent with existing Vue 3 + TypeScript patterns (Composition API, `~/` imports).
- Avoid adding new packages unless explicitly requested.
- Respect SSR vs SPA route rules:
  - “Private” routes are intentionally SPA-only via `routeRules` in `frontend/nuxt.config.ts`.
- Do not allow files to become massive. If they get very big (close to 1000 LOC) or if there is a clean, logical and
project-conventional way to split the logic into components, composables or move things to other parts of the code then
do it.

## Avoid touching

- Generated/vendor artifacts: `frontend/.nuxt/`, `frontend/.data/`, `frontend/node_modules/`, any `*~` files.

