# Jarvis Design System

> Jarvis is an ambient, multi-platform AI assistant: always available, context-aware,
> commandable by text or voice, and able to render useful views instead of only
> returning prose.

This file is the design reference for Jarvis' product language, visual tokens, and
UI patterns.

Canonical source material:

- Visual reference: `docs/claude.design.pdf`
- Prototype/template code: `frontend/design-template/*`
- Core tokens: `frontend/design-template/colors_and_type.css`
- Shell and component styles: `frontend/design-template/jarvis.css`
- Interaction examples: `frontend/design-template/Jarvis.html`,
  `frontend/design-template/ui.jsx`, `frontend/design-template/responses.jsx`,
  `frontend/design-template/panels.jsx`, `frontend/design-template/data.jsx`

If this document conflicts with the shipped frontend implementation, inspect the
current frontend code and template before changing product behavior. For new UI
work, the template is the strongest expression of the intended direction.

---

## 1. Product

Jarvis is a comprehensive personal/work AI assistant. It is not a chat box with
pages around it. It is an ambient operating surface that can:

- answer direct questions
- accept commands
- listen from multiple input sources
- wake itself for scheduled or event-driven updates
- remember user preferences and context
- show structured views such as schedules, maps, galleries, memory, and history

The product should feel calm, capable, and present. It should read like a tool
that is already in the room with the user: monitoring relevant context, waiting
quietly, and turning intent into the right interface.

The core promise:

> Ask, command, or let Jarvis surface what matters.

The design direction is described in the template as **Futurism 26**: architectural
D-DIN typography, hazy glass surfaces, restrained blue/violet intelligence accents,
and a minimal rounded-triangle brand mark.

---

## 2. Experience Principles

### Ambient first

The default state is useful even before the user asks anything. Idle mode shows
time, date, greeting, and compact glance cards for location/weather, next event,
parcel status, and systems.

### Interface, not transcript

Jarvis chooses a response format based on intent. A request for devices becomes a
network map. A calendar question becomes a schedule. A photo request becomes a
gallery. Text answers are still available, but they are only one response mode.

### One continuous relationship

Memory and history are first-class surfaces. The UI should make it clear that
Jarvis carries context across one continuous conversation, while still allowing
users to correct, forget, replay, or inspect what it knows.

### Calm intelligence

The assistant can be proactive, but it should not feel noisy. Status, motion, glow,
and event toasts are quiet and specific. Avoid attention-grabbing loops,
high-saturation backgrounds, and novelty interactions.

### Multi-source input

The top bar and dock model input from "This screen", "Phone", and "Office mic".
The active source is visible, and response headers preserve where the request came
from.

---

## 3. Voice and Content

**Voice:** concise, direct, observant, and calm. Jarvis should sound like it has
already filtered the noise.

**Person:** the assistant may speak in first person when describing its own
actions ("I'll watch error rates"), and second person when referring to the user
or schedule ("Your morning brief is ready").

**Tone samples from the template:**

- "Ask or command..."
- "Good afternoon, Alex. Everything's calm - ask me anything, or tap a thread."
- "Here's the short version - I've pulled what's relevant and left out the noise."
- "Kept on-device and always in play across this one continuous conversation."
- "Motion at the front door - A delivery courier."
- "Health looks nominal. I'll watch error rates."

**Casing:**

| Surface | Treatment | Example |
| --- | --- | --- |
| Product name | Title case | `Jarvis` |
| Display headings | Title case or sentence case | `Memory`, `History` |
| Eyebrows and labels | Uppercase, tracked | `LISTENING · IDLE`, `ONE LONG CONVERSATION` |
| Data labels | Uppercase, condensed | `NEXT UP`, `SYSTEMS`, `PHONE` |
| Body copy | Sentence case | `Everything's calm...` |
| Commands | Verb-first, natural | `Show the home network` |

**Content rules:**

- Prefer short, useful phrases over explanatory copy.
- Use 24-hour time where the user preference indicates it.
- Use metric units in examples.
- Avoid emoji in product UI.
- Avoid jokey placeholder copy.
- Do not over-explain common controls.
- Proactive messages should name the source and reason.

---

## 4. Visual Language

Jarvis uses a cool, glassy, high-precision interface language:

- hazy light/dark grounds
- translucent panels with backdrop blur
- fine hairline borders
- blue-to-violet intelligence accents
- tabular condensed data typography
- rounded-triangle mark and geometric status indicators
- responsive canvas views that morph between answer types

The UI should feel more like a personal command surface than a marketing website.
Avoid hero-page tropes, decorative blobs, thick cards, and generic SaaS gradients.

---

## 5. Color

### 5.1 Accent primitives

| Token | Hex | Role |
| --- | --- | --- |
| `--blue-400` | `#6E8CFF` | dark-theme primary accent |
| `--blue-500` | `#3B6CFF` | light-theme primary accent |
| `--blue-600` | `#2A53E6` | stronger blue |
| `--violet-400` | `#B27DFF` | dark-theme secondary accent |
| `--violet-500` | `#9B5CFF` | light-theme secondary accent |
| `--violet-600` | `#7E3FE6` | stronger violet |
| `--accent-gradient` | `linear-gradient(118deg, #3B6CFF 0%, #9B5CFF 100%)` | primary CTA, active mark, hub nodes |
| `--accent-gradient-soft` | `linear-gradient(118deg, rgba(59,108,255,.16), rgba(155,92,255,.16))` | accent wash |

### 5.2 Status

| Token | Hex | Role |
| --- | --- | --- |
| `--ok-500` | `#36B98A` | available, online, healthy |
| `--warn-500` | `#D79A45` | watch item, scheduled risk |
| `--danger-500` | `#E0635B` | error, destructive state |

Status colors are muted. They should support the interface, not dominate it.

### 5.3 Light theme

| Token | Value | Role |
| --- | --- | --- |
| `--bg` | `#ECEAE5` | warm hazy page ground |
| `--bg-2` | `#F4F2EE` | raised ground |
| `--surface` | `rgba(255,255,255,.62)` | glass panels |
| `--surface-2` | `rgba(255,255,255,.78)` | stronger glass |
| `--surface-solid` | `#FBFAF8` | solid controls |
| `--fg` | `#16171B` | primary text |
| `--fg-2` | `#56585F` | secondary text |
| `--fg-3` | `#8A8C94` | tertiary text/placeholders |
| `--line` | `rgba(22,23,27,.12)` | standard border |
| `--line-strong` | `rgba(22,23,27,.22)` | hover/strong border |
| `--hairline` | `rgba(22,23,27,.07)` | subtle separators |
| `--tint` | `rgba(59,108,255,.06)` | active state fill |
| `--glass-edge` | `rgba(255,255,255,.7)` | glass highlight |
| `--glass-fill` | `rgba(255,255,255,.55)` | defined glass card base |

### 5.4 Dark theme

| Token | Value | Role |
| --- | --- | --- |
| `--bg` | `#08090C` | deep near-black ground |
| `--bg-2` | `#0E1015` | raised ground |
| `--surface` | `rgba(255,255,255,.045)` | glass panels |
| `--surface-2` | `rgba(255,255,255,.07)` | stronger glass |
| `--surface-solid` | `#14161C` | solid controls |
| `--fg` | `#F2F3F6` | primary text |
| `--fg-2` | `#A4A7B2` | secondary text |
| `--fg-3` | `#666A76` | tertiary text/placeholders |
| `--line` | `rgba(255,255,255,.11)` | standard border |
| `--line-strong` | `rgba(255,255,255,.2)` | hover/strong border |
| `--hairline` | `rgba(255,255,255,.06)` | subtle separators |
| `--tint` | `rgba(110,140,255,.08)` | active state fill |
| `--glass-edge` | `rgba(255,255,255,.12)` | glass highlight |
| `--glass-fill` | `rgba(24,26,34,.5)` | defined glass card base |

Dark is the default in the reference HTML (`data-theme="dark"`), but both themes
are fully defined and must remain usable.

### 5.5 Ground and atmosphere

The app background uses `--bg` plus two quiet radial washes:

- violet from the top-right
- blue from the lower-left

The outlined brand mark can sit as a very low-opacity watermark in the lower-right
of the app shell. Keep it subtle; it is atmosphere, not illustration.

---

## 6. Typography

### 6.1 Families

| Family            | Role                                   | Source                                                 |
|-------------------|----------------------------------------|--------------------------------------------------------|
| `D-DIN Exp`       | display headings, brand, large prompts | `frontend/design-template/fonts/D-DINExp*.woff2`       |
| `D-DIN`           | body, controls, readable UI text       | `frontend/design-template/fonts/D-DIN*.woff2`          |
| `D-DIN Condensed` | labels, metadata, time, compact data   | `frontend/design-template/fonts/D-DINCondensed*.woff2` |

CSS aliases:

```css
--font-display: "D-DIN Exp", "D-DIN", system-ui, sans-serif;
--font-sans: "D-DIN", system-ui, sans-serif;
--font-data: "D-DIN Condensed", "D-DIN", system-ui, sans-serif;
```

### 6.2 Type scale

| Token         | Value                    | Role                            |
|---------------|--------------------------|---------------------------------|
| `--t-display` | `clamp(48px, 6vw, 84px)` | idle clock, hero-scale readouts |
| `--t-h1`      | `clamp(36px, 4vw, 56px)` | major page/view title           |
| `--t-h2`      | `clamp(27px, 3vw, 38px)` | section heading                 |
| `--t-h3`      | `22px`                   | card heading                    |
| `--t-body-lg` | `19px`                   | lead text                       |
| `--t-body`    | `16px`                   | body                            |
| `--t-sm`      | `14px`                   | small text                      |
| `--t-label`   | `12px`                   | labels and eyebrows             |

Line-height tokens:

| Token        | Value  | Role       |
|--------------|--------|------------|
| `--lh-tight` | `1.04` | display    |
| `--lh-snug`  | `1.2`  | headings   |
| `--lh-body`  | `1.55` | paragraphs |

Tracking:

- Display: `-0.01em`
- H2: `-0.005em`
- Labels: `0.18em`
- Data: `0.01em`, tabular numerics

Labels are always uppercase, condensed, and tracked. Data-heavy surfaces should
use `font-variant-numeric: tabular-nums`.

---

## 7. Spacing, Radius, Shadow, Glass

### 7.1 Spacing

Jarvis uses a 4px base scale:

| Token    | Px      |
|----------|---------|
| `--s-1`  | `4px`   |
| `--s-2`  | `8px`   |
| `--s-3`  | `12px`  |
| `--s-4`  | `16px`  |
| `--s-5`  | `24px`  |
| `--s-6`  | `32px`  |
| `--s-7`  | `48px`  |
| `--s-8`  | `64px`  |
| `--s-9`  | `96px`  |
| `--s-10` | `128px` |

### 7.2 Radii

| Token      | Value   | Role                                   |
|------------|---------|----------------------------------------|
| `--r-xs`   | `6px`   | keyboard hints, small detail           |
| `--r-sm`   | `10px`  | compact icon wells                     |
| `--r-md`   | `14px`  | buttons, rows, controls                |
| `--r-lg`   | `20px`  | large icons, gallery tiles             |
| `--r-xl`   | `28px`  | cards, command palette, large surfaces |
| `--r-pill` | `999px` | dock, chips, source pills              |

### 7.3 Shadows

| Token         | Value                                                           | Role                           |
|---------------|-----------------------------------------------------------------|--------------------------------|
| `--shadow-sm` | `0 1px 2px rgba(20,22,30,.06), 0 2px 6px rgba(20,22,30,.05)`    | controls                       |
| `--shadow-md` | `0 4px 14px rgba(20,22,30,.08), 0 12px 34px rgba(20,22,30,.07)` | cards and dock                 |
| `--shadow-lg` | `0 18px 60px rgba(20,22,30,.14)` in light, deeper in dark       | sheets and palette             |
| `--glow`      | accent ring plus colored shadow                                 | focused input, selected device |

### 7.4 Glass

Glass is a primary material:

- Background: `--glass-fill` or `--surface`
- Border: `1px solid var(--line)`
- Highlight: inset `0 1px 1px var(--glass-edge)`
- Blur: `backdrop-filter: blur(20px-40px) saturate(150%-190%)`
- Optional diagonal shine via `::before`

Use glass for the rail, topbar, cards, dock, command palette, sheets, and event
toasts. Use `--surface-solid` for controls that need stronger contrast inside
glass.

---

## 8. Layout

### 8.1 App shell

The reference app is full viewport and non-document-like:

- `.app`: `display: flex`, `height: 100vh`
- `.rail`: fixed-width left rail, `78px`
- `.main`: flex column
- `.topbar`: `70px` high
- `.canvas-wrap`: flexible middle region
- `.dock`: bottom input surface

The body intentionally uses `overflow: hidden`; scroll belongs inside canvas
views, sheets, and palettes.

### 8.2 Rail

The rail contains:

- brand mark button
- home
- memory
- history
- spacer
- theme toggle

Rail buttons are 48x48 with `--r-md`. Active buttons use `--tint`, accent text,
and a border. The rail should remain calm and icon-led.

### 8.3 Topbar

The topbar contains:

- brand stack: `Jarvis` plus live status (`LISTENING · IDLE`, `WORKING`, `ACTIVE`)
- source pills (`This screen`, `Phone`, `Office mic`)
- command/search affordance with `Cmd/Ctrl+K`
- theme icon button

Hide source pills on narrower layouts as the template does under `980px`.

### 8.4 Canvas

The canvas is the morphing response region. It must support:

- idle ambient dashboard
- thinking state
- text answer
- gallery
- device/network map
- calendar/schedule
- memory
- history

Keep the canvas spacious. Let views use grids, cards, and panels instead of
turning every response into prose.

### 8.5 Dock

The dock is the primary input surface:

- pill glass container
- Jarvis mark
- text input or live waveform
- mic button
- send button
- hint row for commands, voice, and proactive events

The dock can show event toasts above it. Toasts are short, source-specific, and
temporary.

---

## 9. Motion

Motion is part of Jarvis' sense of presence, but it should stay controlled.

| Token    | Value                         | Role              |
|----------|-------------------------------|-------------------|
| `--ease` | `cubic-bezier(.22,.61,.36,1)` | standard easing   |
| `--dur`  | `.42s`                        | standard duration |

Motion patterns:

- Brand mark breathes in idle mode.
- Status LEDs breathe.
- Thinking state uses drifting rounded triangles under a morphing glass pane.
- Response cards enter with short rise/morph animations.
- Command palette fades/rises in.
- Sheets slide in from the right.
- Buttons scale slightly on press.
- Waveform bars animate while listening.

Reduced motion must be respected:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

Avoid bouncy physics, aggressive parallax, or constant decorative motion unrelated
to system state.

---

## 10. Iconography and Brand Mark

### 10.1 Icons

The template uses Lucide icons through `window.lucide` and a small React wrapper.
For the Nuxt implementation, continue using the existing icon strategy where
available, but keep the visual style aligned with Lucide:

- outline icons
- rounded caps and joins
- simple geometry
- approximately `1.75` stroke width in the template
- 14-22px for controls
- larger 24-32px icons in maps/cards where needed

No icon fonts. Avoid emoji-as-icons.

### 10.2 Brand mark

The Jarvis mark is a rounded triangle:

- gradient: `#3B6CFF` to `#9B5CFF`
- rounded stroke and joins
- used in the rail, dock, idle breath state, thinking animation, and low-opacity
  watermark

Assets live in `frontend/design-template/assets/`:

- `mark.svg`
- `mark-dark.svg`
- `mark-light.svg`
- `mark-outline.svg`

The mark is not a decorative logo lockup. It acts like a system presence indicator.

---

## 11. Component Patterns

### 11.1 Buttons

| Variant     | Style                                                    | Usage                    |
|-------------|----------------------------------------------------------|--------------------------|
| Primary     | `--accent-gradient`, white text, `--r-md`, subtle shadow | send, main actions       |
| Secondary   | `--surface-2`, `--line`, blurred/glass feel              | regular actions          |
| Ghost       | transparent, secondary text                              | low-emphasis actions     |
| Icon button | 44x44, `--r-md`, border, glass/solid fill                | topbar and view controls |
| Dock button | 42x42 circle                                             | mic and send             |

Buttons should press with a slight scale, not a dramatic animation.

### 11.2 Cards

Base cards:

- `border-radius: var(--r-xl)`
- `padding: 24px`
- `background: var(--glass-fill)`
- `backdrop-filter: blur(24px) saturate(160%)`
- `border: 1px solid var(--line)`
- `box-shadow: var(--shadow-md), inset 0 1px 1px var(--glass-edge)`

Use `.card.solid` when blur would reduce readability or when a view needs a
stronger information panel.

### 11.3 Badges and chips

Badges use condensed uppercase text and pill shapes:

- `ok`: success/online
- `warn`: watch item
- `dng`: danger/error
- `acc`: accent/active
- `neu`: neutral metadata

Chips are interactive prompt/actions. They can lift by 1px on hover and should
show the accent on their icon.

### 11.4 Command palette

The command palette is a centered glass modal:

- opens with `Cmd/Ctrl+K`
- grouped sections (`Ask Jarvis`, `Simulate event`, `Controls`)
- keyboard navigable
- selected item uses `--tint` and accent text
- closes on Escape or outside click

It is both a command launcher and a discoverable list of common capabilities.

### 11.5 Sheets

Slide-over sheets use:

- right-side fixed placement
- width `min(440px, 92vw)`
- high blur glass
- left border
- `--shadow-lg`

Use sheets for inspector/detail workflows, not for primary response views that
belong in the canvas.

---

## 12. Response Views

### 12.1 Idle

Idle is the ambient home state:

- breathing brand mark
- large tabular clock
- uppercase date label
- greeting with the user's name
- glance cards for weather/location, next event, parcel, and systems

Idle should feel useful and restful. It is not an empty state.

### 12.2 Thinking

Thinking shows work in progress:

- rounded triangle elements drifting under glass
- current step label
- step chips: parsing request, recalling context, reasoning, composing view

This state communicates that Jarvis is assembling a view, not just waiting on a
spinner.

### 12.3 Text answer

Text answers use:

- large lead paragraph in display type
- typewriter reveal for the lead
- triangular bullets for key points
- compact source pills

Use text answers for synthesis, status, and explanation. Keep them concise.

### 12.4 Gallery

Gallery responses use a visual grid:

- featured tile spans two cells on desktop
- image tiles with overlay captions on hover
- compact result count badge and source metadata

The template uses gradients as placeholders. Production galleries should use real
images when the user is inspecting photos or visual results.

### 12.5 Device/network map

Network responses use:

- map canvas with connected nodes
- central hub node in the accent gradient
- edge device nodes with online/warn/offline indicators
- side list/detail panel on desktop
- single-column view under `980px`

Selection should be obvious through accent stroke/glow, not through heavy fills.

### 12.6 Calendar/schedule

Schedule responses use:

- time grid
- current-time line
- event cards with subtle tone-specific left borders
- side panel for next event
- event count badge

Calendar UI should be scannable at a glance.

### 12.7 Memory

Memory is a main canvas view, not a hidden settings page:

- summary card with ring gauge
- grouped memory cards
- metadata labels for stability, updates, and active rules

Memory copy should be explicit about scope and control: users can correct or
forget stored context.

### 12.8 History

History is grouped by recency and context:

- columns/cards per time period or topic
- timestamps in condensed data type
- response type labels
- tags for channel/context
- replay affordance

History supports the "one continuous conversation" model.

---

## 13. Responsiveness

The reference breakpoint is `980px`:

- source pills hide
- network and calendar views collapse to one column
- side panels inside those views hide
- gallery becomes a two-column grid
- featured gallery tile spans both columns

All primary controls must remain reachable on smaller screens. Avoid fixed-width
content that causes horizontal overflow inside the canvas.

---

## 14. Accessibility and States

Required states:

- idle
- listening
- working/thinking
- active answer
- selected item
- hover
- pressed
- focus
- empty/no matches
- reduced motion

Guidance:

- Use semantic buttons for interactive controls.
- Provide `title`/accessible labels for icon-only buttons.
- Maintain contrast across both light and dark themes.
- Do not rely only on color for status; pair color with text labels or icons.
- Keep keyboard access for the command palette and input dock.
- Respect `prefers-reduced-motion`.

---

## 15. Imagery

Jarvis is primarily an interface system. Use imagery only when the task is about
visual content, such as photo galleries, camera events, maps, or generated/attached
assets.

For inspectable visual content:

- show the subject clearly
- avoid abstract stand-ins in production
- preserve captions and metadata
- support larger/open states when needed

For non-visual answers, prefer structured UI: cards, maps, timelines, source pills,
and concise text.

---

## 16. Codebase Wiring

Current monorepo shape:

| Concern              | Where                                                   |
|----------------------|---------------------------------------------------------|
| Frontend app         | `frontend/`                                             |
| Nuxt config          | `frontend/nuxt.config.ts`                               |
| Frontend pages       | `frontend/pages/`                                       |
| Frontend components  | `frontend/components/`                                  |
| Frontend composables | `frontend/composables/`                                 |
| Frontend state       | `frontend/store/`                                       |
| Frontend styling     | `frontend/assets/style/`, `frontend/tailwind.config.ts` |
| Design template      | `frontend/design-template/`                             |
| Backend API          | `backend/`                                              |
| Docs                 | `docs/`                                                 |

Template-specific wiring:

| Concern                      | File                                           |
|------------------------------|------------------------------------------------|
| Color, type, theme tokens    | `frontend/design-template/colors_and_type.css` |
| App shell and components     | `frontend/design-template/jarvis.css`          |
| Prototype shell              | `frontend/design-template/Jarvis.html`         |
| UI primitives                | `frontend/design-template/ui.jsx`              |
| Mock data and intent routing | `frontend/design-template/data.jsx`            |
| Response views               | `frontend/design-template/responses.jsx`       |
| Memory/history/palette       | `frontend/design-template/panels.jsx`          |
| Brand mark assets            | `frontend/design-template/assets/`             |
| Fonts                        | `frontend/design-template/fonts/`              |

Implementation note: the template is React for design exploration, while the
production frontend is Nuxt 3 with Vue 3 and TypeScript. Port patterns, tokens,
and behavior into Vue rather than copying React architecture directly.

---

## 17. Do and Don't

Do:

- Build the usable assistant surface first.
- Preserve the ambient idle state.
- Render structured views when they are more useful than text.
- Keep Memory and History visible and understandable.
- Use D-DIN roles consistently.
- Support light and dark themes from the same token set.
- Keep motion tied to state.
- Use glass, liquid glass, hairlines, and subtle glow with restraint.

Don't:

- Make the app feel like a generic SaaS landing page.
- Turn every answer into a chat transcript.
- Use emoji as product UI.
- Use purple/blue blobs as a substitute for interface structure.
- Add heavy hover lifts to information cards.
- Hide proactive events without source or reason.
- Break reduced-motion behavior.

