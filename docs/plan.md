Below is a phased development plan based on the notes in your images. I read them as:

**Phase 1:** local physical server; headless STT/ASR and TTS; external/vLLM-style model APIs; local web UI over VPN/ZeroTier; memory system; web search; calendar/time APIs; scheduled events; LLM calls.
**Phase 2:** fully local LLM; filesystem I/O; Gmail/Viber/WhatsApp/Telegram read-only access; triggered events such as new email.
**Phase 3:** self-extending code and event modules; remote clients/workers such as Android/phone/PC, camera, mic offerings.
**Phase 4:** agent spawning and orchestration — stub only.
**Phase 5:** custom memory database and graph intelligence abstraction — stub only.

## 1. Product strategy: get useful fast

The project should be built as a **local-first personal assistant platform**, not as a big “AGI assistant” from day one. Every phase should ship a vertical slice that you actually use daily.

The key principle: **read-only first, narrow write permissions later, autonomous action last**.

Early usefulness should come from:

1. voice-in / voice-out access on your local server;
2. a reliable web UI reachable privately;
3. personal memory and reminders;
4. calendar/time/search tools;
5. later, local models and read-only inbox/chat awareness;
6. later still, safe self-extension through reviewed modules.

Use a provider abstraction from the beginning. vLLM has an OpenAI-compatible server, supports structured outputs, and documents tool-calling/reasoning parser support, so it fits well as one backend behind a generic model gateway. Ollama and llama.cpp also expose OpenAI-compatible APIs, which makes later migration to local models much easier. ([vLLM][1])

## 2. Recommended architecture

Think of the system as a set of small services, not one giant agent.

```text
User
 ├─ Web UI over VPN
 ├─ Voice UI
 ├─ Mobile/desktop remote clients
 │
Assistant API
 ├─ Conversation service
 ├─ Tool registry
 ├─ Event bus
 ├─ Scheduler
 ├─ Memory service
 ├─ Connector service
 ├─ Model gateway
 └─ Audit log

Model Gateway
 ├─ External LLM APIs
 ├─ vLLM
 ├─ Ollama
 └─ llama.cpp

Local Capabilities
 ├─ STT/ASR
 ├─ TTS
 ├─ File tools
 ├─ Calendar/search/time tools
 ├─ Gmail/chat read-only tools
 └─ Sandboxed code/module runner
```

For speech, start with a boring, proven local pipeline. Whisper is a general-purpose multilingual speech recognition model, and Piper is a fast local neural TTS system, so the first version can be fully local for voice even before the LLM is local. ([GitHub][2])

For remote access, keep the assistant off the public internet. ZeroTier’s documentation explicitly covers hosting a local website accessible only through your network, which matches your note about a local web UI over VPN/ZeroTier. ([docs.zerotier.com][3])

For memory, use a practical two-layer setup first: an append-only event journal plus a graph database. Memgraph is an open-source graph database with Cypher support and Python client documentation, so it is a reasonable first graph memory backend before you attempt a custom memory database in Phase 5. ([memgraph.com][4])

Use MCP-style design ideas, but do not overbuild around MCP at the start. The Model Context Protocol formalizes how tools expose external systems to models, which is useful for your future module/tool registry, but your first implementation can be simple internal Python tools with strict schemas. ([Model Context Protocol][5])

## 3. Human + multi-agent development model

You are the **product owner, security approver, and final merger**. The AI agents should not be uncontrolled runtime agents yet; they are development collaborators.

Use these development agents:

| Agent              | Responsibility                                          | Output                           |
|--------------------|---------------------------------------------------------|----------------------------------|
| Product/PM Agent   | Breaks phases into tickets, tracks acceptance criteria  | GitHub issues, milestone plan    |
| Architect Agent    | Defines interfaces, service boundaries, ADRs            | Architecture docs, API contracts |
| Research Agent     | Checks current docs/API limits before implementation    | Research briefs with citations   |
| Backend Agent      | Assistant API, event bus, scheduler, tool registry      | Backend PRs                      |
| Voice Agent        | ASR/TTS pipeline, audio capture/playback, latency tests | Speech service PRs               |
| Memory Agent       | Journal, summaries, graph memory, retrieval             | Memory service PRs               |
| Integrations Agent | Calendar, Gmail, Telegram, Viber, WhatsApp connectors   | Connector PRs                    |
| UI Agent           | Web UI, settings, logs, approvals                       | Frontend PRs                     |
| DevOps Agent       | Docker Compose, VPN docs, backups, observability        | Infra PRs                        |
| QA/Eval Agent      | Test plans, regression prompts, local model evals       | Test reports                     |
| Security Agent     | Permissions, sandboxing, threat reviews                 | Security review per PR           |
| Docs Agent         | Setup guide, runbooks, user manual                      | Documentation PRs                |

Every ticket should follow this workflow:

```text
1. PM Agent creates ticket.
2. Research Agent checks docs and constraints.
3. Architect Agent confirms interface.
4. Implementation Agent codes in branch.
5. QA Agent writes/runs tests.
6. Security Agent reviews permissions and secrets.
7. Human reviews and merges.
8. Release Agent updates changelog and deploy notes.
```

No development agent should receive production secrets. Agents may write code, tests, docs, and configs, but only the human applies credentials, deploys sensitive integrations, and enables dangerous capabilities.

## 4. Security rules from day one

This assistant will eventually touch microphones, files, messages, calendar, code, and possibly cameras. Security cannot be a later feature.

Minimum rules:

1. **No public exposure** of the web UI in Phase 1.
2. **All tools are permissioned**: read calendar, read email, read files, write files, send messages, run code, deploy modules are separate permissions.
3. **Everything is logged**: prompt, tool call, arguments, result summary, model used, user approval status.
4. **Autonomous writes are disabled** until explicitly allowed per tool.
5. **Code generation runs only in a sandbox**.
6. **Secrets never enter prompts** unless absolutely required, and even then through redacted tool wrappers.

This is especially important because agent tools and plugin systems can execute arbitrary code. Open WebUI’s own docs warn that tools/functions execute arbitrary Python code and should only be installed from trusted sources. OWASP’s LLM Top 10 includes prompt injection, sensitive information disclosure, supply-chain risk, excessive agency, and unbounded consumption, all of which directly apply to a personal assistant with tools. Docker’s own security docs also warn about the Docker daemon attack surface and root privileges, so rootless/sandboxed execution should be preferred for agent-generated code. ([Open WebUI][6])

## 5. Phase 0 — foundation before Phase 1

This is not in your notebook, but it should exist as a small setup phase.

### Goal

Create the repo, local dev environment, interfaces, and deployment skeleton.

### Deliverables

* Monorepo with `/services`, `/clients`, `/docs`, `/infra`, `/tests`.
* Docker Compose for local development.
* `.env.example`, secrets policy, backup policy.
* Assistant API skeleton.
* Model gateway interface.
* Tool interface.
* Event interface.
* Memory interface.
* Audit log schema.
* CI checks: lint, type check, unit tests.
* ADR folder for decisions.

### Minimal core interfaces

```python
ModelProvider.generate(messages, tools=None, response_schema=None)
Tool.run(user_id, arguments, permission_context)
Memory.write_event(event)
Memory.search(query, filters)
Scheduler.schedule(event)
Connector.sync(source)
```

### Definition of done

You can run one command, open the local API, send a test message to an external LLM, and see the full interaction stored in the audit log.

## 6. Phase 1 — useful local server, voice, web UI, memory, search, calendar, scheduled events

### Phase 1 goal

By the end of Phase 1, the assistant should already be useful every day:

* talk to it locally;
* access it from your devices over private network;
* ask it calendar/time/search questions;
* set reminders;
* store and retrieve useful personal/project memory;
* use external model APIs while the local server handles orchestration.

### Phase 1.1 — local server and Assistant API

Build the local headless server first.

Services:

* `assistant-api`
* `model-gateway`
* `event-store`
* `scheduler`
* `memory-service`
* `web-ui`

Start with FastAPI or equivalent, SQLite/Postgres for state, and a simple queue. Avoid distributed complexity unless needed.

Acceptance test:

```text
Given the server is running,
when I send "remind me tomorrow at 9 to review the AI assistant plan",
then the system stores the request, schedules the reminder, and logs the action.
```

### Phase 1.2 — model gateway with external/vLLM-compatible APIs

Create one unified model interface. Do not scatter direct OpenAI/vLLM/Ollama calls across the codebase.

The gateway should support:

* chat completion;
* structured JSON output;
* tool call planning;
* streaming responses;
* model routing;
* request logging;
* cost/latency tracking.

Recommended starting policy:

```text
fast_model: cheap/fast external model
smart_model: stronger external model
local_model: stub until Phase 2
```

Acceptance test:

```text
The same assistant request can run against provider A or provider B without changing tool code.
```

### Phase 1.3 — local ASR/STT and TTS

Start with push-to-talk or recorded audio, not always-on wake word. Always-on audio can come later.

Pipeline:

```text
Audio input
 → ASR
 → text request
 → assistant response
 → TTS
 → audio playback
```

Keep ASR/TTS as separate services so they can later run on another worker.

Acceptance tests:

* You can speak a reminder and hear confirmation.
* Transcripts are saved.
* Failed transcription does not trigger actions without confirmation.

### Phase 1.4 — private web UI

Use a simple web UI first. Open WebUI can be evaluated, but disable arbitrary plugin/tool creation for normal use. A custom minimal UI may be safer and easier to reason about.

Required UI features:

* chat;
* voice upload or push-to-talk;
* memory viewer;
* reminders;
* tool-call log;
* approval queue;
* settings;
* model selector.

Expose it only over ZeroTier/VPN in Phase 1.

Acceptance test:

```text
From phone/laptop on private network, open the assistant UI, ask a question, and inspect the tool log.
```

### Phase 1.5 — memory v0

Do not build the custom memory database yet. Use a simple, inspectable design.

Memory layers:

1. **Event journal:** every interaction, tool call, reminder, summary, and user correction.
2. **Facts table:** durable facts about you, projects, preferences, devices, people, systems.
3. **Graph memory:** entities and relationships in Memgraph.
4. **Embeddings/vector search:** optional but useful for notes and conversation recall.
5. **Summaries:** daily/project summaries generated by scheduled jobs.

Initial graph entities:

```text
Person
Project
Task
Event
Device
File
Conversation
Reminder
Capability
Tool
Source
Decision
```

Initial relationships:

```text
WORKS_ON
MENTIONED_IN
DEPENDS_ON
SCHEDULED_FOR
OWNED_BY
CONNECTED_TO
CREATED_BY
SUMMARIZED_BY
```

Acceptance tests:

* Ask: “What did I decide about Phase 1 yesterday?”
* Ask: “What are the open tasks for the assistant project?”
* Correct a memory and verify the old memory is not silently deleted but superseded.

### Phase 1.6 — web search, calendar, and time tools

Build these as read-only tools first.

Tools:

```text
get_current_time(location)
search_web(query)
read_calendar_range(start, end)
get_next_calendar_event()
summarize_calendar_day(date)
```

Google Calendar has a full API reference and supports push notifications later, but Phase 1 only needs read access and free/busy/calendar range queries. ([Google for Developers][7])

Acceptance tests:

* “What is my next event?”
* “What do I have tomorrow?”
* “Research X and summarize with sources.”
* “Remind me 30 minutes before my next meeting.”

### Phase 1.7 — scheduled events and LLM calls

Create a local scheduler that can run:

* reminders;
* daily summaries;
* recurring checks;
* deferred LLM calls;
* memory consolidation;
* calendar lookahead.

Scheduled event schema:

```yaml
id:
type: reminder | summary | check | llm_task
status: pending | running | done | failed | cancelled
run_at:
recurrence:
input:
requires_approval:
created_by:
audit_log_id:
```

Acceptance tests:

* Reminder fires.
* Daily summary is generated.
* Failed scheduled task retries safely.
* Every scheduled LLM call is visible in logs.

### Phase 1 final acceptance

Phase 1 is complete when you can use the assistant for:

```text
- voice question answering;
- reminders;
- calendar lookup;
- web research;
- project memory;
- daily summary;
- private web access;
- full auditability.
```

## 7. Phase 2 — local LLM, filesystem I/O, read-only communications, triggered events

### Phase 2 goal

Make the assistant more private, more autonomous in observation, and more useful with personal context.

Phase 2 should not mean “let it do everything.” It means:

* run capable local models;
* let the assistant read approved files;
* let it read approved communication sources;
* react to events;
* still require approval for external side effects.

### Phase 2.1 — fully local LLM

Add local model backends behind the same Phase 1 gateway.

Recommended backend split:

| Backend       | Use                                         |
|---------------|---------------------------------------------|
| Ollama        | easiest local model management              |
| llama.cpp     | efficient quantized CPU/GPU local inference |
| vLLM          | stronger GPU server throughput              |
| external APIs | fallback for hard tasks                     |

Because these expose OpenAI-compatible APIs, your application code should not need major changes when switching between external and local inference. ([Ollama Docs][8])

Add an eval harness before trusting local models:

```text
- reminder extraction
- calendar question answering
- memory retrieval
- tool call JSON validity
- summarization quality
- refusal to execute unsafe actions
- latency and VRAM/RAM usage
```

Acceptance test:

```text
For 50 saved assistant tasks, compare local_model vs external_model and route automatically based on quality/latency.
```

### Phase 2.2 — filesystem I/O

Start read-only.

Filesystem model:

```text
/assistant_workspace/read_only
/assistant_workspace/staging
/assistant_workspace/generated
/assistant_workspace/quarantine
```

Capabilities:

```text
list_files
read_file
summarize_file
search_files
extract_tasks_from_file
propose_file_change
```

Do not allow arbitrary filesystem access. Do not allow direct writes to personal directories. Generated changes should be staged as patches or new files for review.

Acceptance tests:

* “Summarize this project folder.”
* “Find files related to Memgraph memory.”
* “Propose changes to this config,” but not directly overwrite it.

### Phase 2.3 — Gmail read-only connector

Use Gmail read-only first, then event triggers.

Capabilities:

```text
search_email
read_email
summarize_thread
extract_tasks_from_email
detect_urgent_email
```

Gmail API supports push notifications through Pub/Sub, allowing the backend to watch mailbox changes without polling. ([Google for Developers][9])

Acceptance tests:

* “Summarize unread emails from today.”
* “Show urgent emails.”
* “When a new email from X arrives, notify me.”
* No email is sent or archived in Phase 2 unless you explicitly add that later.

### Phase 2.4 — Telegram, WhatsApp, Viber read-only/event connectors

Treat these differently because their official APIs differ.

Telegram Bot API supports receiving updates either through polling with `getUpdates` or webhooks. WhatsApp Business Platform uses webhooks for events, and Viber Bot API also uses webhooks for callbacks/user messages; Viber bot creation may involve commercial terms, so verify feasibility before committing to it. ([Telegram][10])

Important boundary: do not scrape personal messaging apps with unofficial hacks. Start only with official APIs, export files, bot chats, or user-forwarded messages.

Connector priority:

1. Gmail — highest value, official, mature.
2. Telegram bot — easy event integration.
3. WhatsApp Cloud API — useful but more business-account oriented.
4. Viber bot — possible, but verify account/API constraints.
5. Personal chat app scraping — avoid unless manually exported.

Acceptance tests:

* New Telegram bot message triggers an assistant event.
* WhatsApp/Viber feasibility documented before implementation.
* Assistant can summarize only messages it is allowed to see.

### Phase 2.5 — triggered events

Create a unified event model:

```yaml
event_type:
  - new_email
  - calendar_changed
  - telegram_message
  - file_changed
  - scheduled_time
  - manual_request

source:
payload:
dedupe_key:
priority:
requires_llm:
requires_approval:
```

Example automations:

```text
When new email arrives from important contact:
  summarize it
  check calendar relevance
  notify user

Every morning:
  summarize calendar
  summarize unread priority messages
  list open reminders

When file changes in project folder:
  update memory index
  extract TODOs
```

Acceptance tests:

* Events are deduplicated.
* Events can be replayed.
* Event handlers are idempotent.
* Triggered LLM calls are logged.
* Notifications do not become spam.

### Phase 2 final acceptance

Phase 2 is complete when:

```text
- a local model can handle common tasks;
- external models remain available as fallback;
- approved files can be read and summarized;
- Gmail can be read and watched;
- at least one chat connector can trigger events;
- event-driven summaries are useful;
- no write/send actions happen without approval.
```

## 8. Phase 3 — self-extending modules and remote clients/workers

### Phase 3 goal

Add a controlled way for the assistant to extend its own capabilities, plus remote devices/workers that offer sensors or compute.

This must not be “the assistant edits itself live.” It should be:

```text
assistant proposes module
 → sandbox builds module
 → tests run
 → security review
 → human approval
 → module installed disabled
 → human enables permissions
```

OpenAI’s agent sandbox guidance describes sandboxes as appropriate when an agent needs to manipulate files, run commands, produce artifacts, expose a service, or continue stateful work. That is the right pattern here: generated code belongs in an isolated workspace, not on the host system. ([OpenAI Developers][11])

### Phase 3.1 — module system

Create a module contract.

Example `module.yaml`:

```yaml
name: gmail_priority_summarizer
version: 0.1.0
description: Summarizes priority Gmail threads
triggers:
  - new_email
permissions:
  - gmail.read
  - memory.write
  - notify.user
denied_permissions:
  - gmail.send
  - filesystem.write
entrypoint: module.py
timeout_seconds: 30
max_daily_runs: 50
requires_approval: false
```

Module lifecycle:

```text
proposed
generated
tested
security_reviewed
approved
installed_disabled
enabled
deprecated
removed
```

Acceptance tests:

* Assistant can draft a module spec.
* Codegen agent can implement it in sandbox.
* QA agent can run tests.
* Security agent can reject risky permissions.
* Human can approve/reject in UI.
* Runtime only loads approved modules.

### Phase 3.2 — self-extending code workflow

The assistant may create:

* new read-only tools;
* new event handlers;
* new summarizers;
* new parsers;
* new UI widgets;
* new scheduled jobs;
* connector adapters.

The assistant may not directly:

* modify production code;
* deploy itself;
* access secrets;
* grant itself permissions;
* bypass tests;
* enable modules without human approval.

Self-extension prompt policy:

```text
You are allowed to propose and implement a module only inside the sandbox.
You must produce:
1. module.yaml
2. source code
3. tests
4. security notes
5. rollback notes
6. required permissions
You must not request broader permissions than necessary.
```

### Phase 3.3 — remote clients and workers

Remote clients should be capability providers.

Examples:

| Device          | Capabilities                                                     |
|-----------------|------------------------------------------------------------------|
| Android phone   | microphone, camera capture, location with consent, notifications |
| Desktop PC      | filesystem index, browser handoff, local app control later       |
| GPU worker      | local LLM inference, ASR batch jobs, embeddings                  |
| Camera node     | explicit image capture, not continuous surveillance              |
| Microphone node | push-to-talk or explicitly enabled listening                     |

Remote worker protocol:

```yaml
device_id:
owner:
capabilities:
  - mic.capture
  - camera.capture
  - asr.transcribe
  - notify.push
status:
last_seen:
permissions:
network:
```

Start with a simple worker agent:

```text
worker connects to server
 → authenticates
 → advertises capabilities
 → receives job
 → returns result
 → job is logged
```

Acceptance tests:

* Phone can send audio to server.
* PC worker can perform local transcription.
* Server can revoke a worker.
* Worker cannot access jobs outside its permissions.
* Camera/mic capture requires explicit user action.

### Phase 3.4 — event modules

Allow modules to subscribe to event types:

```text
on_new_email
on_calendar_changed
on_file_changed
on_voice_command
on_manual_trigger
on_schedule
on_worker_available
```

Example useful Phase 3 modules:

1. “Email-to-task extractor”
2. “Daily project standup generator”
3. “Meeting prep pack”
4. “Project folder change summarizer”
5. “Voice note to memory”
6. “Research watcher”
7. “Local model quality evaluator”
8. “Device health checker”

### Phase 3 final acceptance

Phase 3 is complete when:

```text
- assistant can propose a new module;
- module is built and tested in sandbox;
- human can approve it;
- approved module can subscribe to events;
- remote worker can offer mic/camera/compute capability;
- permissions are enforced per module and per device.
```

## 9. Phase 4 — stub only

### Phase 4: agent spawning and orchestration

Status: **stub, skipped for now**.

Do not implement yet. Leave interfaces only:

```text
AgentDefinition
AgentRun
AgentCapability
AgentHandoff
AgentBudget
AgentSupervisor
AgentResult
```

Why skip: you can get a lot of value from deterministic services, tools, modules, and event handlers without building full autonomous agent orchestration. LangGraph and the OpenAI Agents SDK both emphasize production agent concerns like durable execution, human-in-the-loop, tracing, tools, guardrails, and state, but those are Phase 4 concerns, not Phase 1–3 blockers. ([LangChain Docs][12])

Keep this placeholder:

```yaml
phase_4_stub:
  name: agent_spawning_and_orchestration
  depends_on:
    - module_system
    - event_bus
    - permissions
    - sandbox
    - audit_log
  implementation_status: skipped
```

## 10. Phase 5 — stub only

### Phase 5: custom memory database and graph intelligence abstraction

Status: **stub, skipped for now**.

Do not build a custom memory database until you have months of real usage data. In Phase 1–3, collect the data that will teach you what the custom memory system should become.

Keep this placeholder:

```yaml
phase_5_stub:
  name: custom_memory_database_and_graph_intelligence
  depends_on:
    - event_journal
    - graph_memory
    - vector_search
    - user_feedback
    - memory_corrections
    - module_event_history
  implementation_status: skipped
```

Future concepts to preserve hooks for:

```text
MemoryObject
MemorySource
MemoryConfidence
MemorySupersession
MemoryDecay
MemoryPrivacyClass
GraphReasoningQuery
PersonalOntology
```

## 11. Suggested milestone timeline

| Milestone  | Outcome                                              |
|------------|------------------------------------------------------|
| Week 1     | Phase 0 repo, API skeleton, model gateway, audit log |
| Week 2     | Phase 1 server, web UI, external model chat          |
| Week 3     | STT/TTS voice loop                                   |
| Week 4     | memory v0, reminders, scheduler                      |
| Week 5     | calendar/time/search tools                           |
| Week 6–7   | local LLM backend and eval harness                   |
| Week 8     | filesystem read-only tools                           |
| Week 9     | Gmail read-only + triggered events                   |
| Week 10    | Telegram or another chat event connector             |
| Week 11–12 | module system sandbox                                |
| Week 13+   | remote workers and self-extension workflow           |


[1]: https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/?utm_source=chatgpt.com "OpenAI-Compatible Server - vLLM Documentation"
[2]: https://github.com/openai/whisper?utm_source=chatgpt.com "openai/whisper: Robust Speech Recognition via Large- ..."
[3]: https://docs.zerotier.com/guides/?utm_source=chatgpt.com "Guides"
[4]: https://memgraph.com/docs/?utm_source=chatgpt.com "Memgraph documentation"
[5]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools?utm_source=chatgpt.com "Tools"
[6]: https://docs.openwebui.com/features/extensibility/plugin/tools/?utm_source=chatgpt.com "Tools"
[7]: https://developers.google.com/workspace/calendar/api/v3/reference?utm_source=chatgpt.com "API Reference | Google Calendar"
[8]: https://docs.ollama.com/api/openai-compatibility?utm_source=chatgpt.com "OpenAI compatibility"
[9]: https://developers.google.com/workspace/gmail/api/guides/push?utm_source=chatgpt.com "Configure push notifications in Gmail API"
[10]: https://core.telegram.org/bots/api?utm_source=chatgpt.com "Telegram Bot API"
[11]: https://developers.openai.com/api/docs/guides/agents/sandboxes?utm_source=chatgpt.com "Sandbox Agents | OpenAI API"
[12]: https://docs.langchain.com/oss/python/langgraph/overview?utm_source=chatgpt.com "LangGraph overview - Docs by LangChain"
