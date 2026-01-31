# Personal Telegram Assistant for Capturing and Organizing Information

This repository defines the product requirements and behavior for a personal
Telegram assistant that captures voice or text, structures it, and helps with
planning and recall. The assistant should feel like a smart secretary:
"Got it, organized it, and will help you remember it on time."

## Quickstart

### 1) Install dependencies

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### 2) Configure environment

Copy `.env.example` to `.env` and fill in:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`

Optional:
- `OPENAI_MODEL` (default: gpt-4o-mini)
- `OPENAI_TRANSCRIBE_MODEL` (default: whisper-1)
- `DB_PATH` (default: ./assistant.db)
- `TIMEZONE` (default: UTC)
- `LOCALES` (default: en,ru)

### 3) Run the bot

```
python main.py
```

### 4) Run tests

```
pytest
```

### Commands

- `/plan_today` - show items due today
- `/plan_week` - show items due this week
- `/tasks [context]` - list open tasks
- `/search <query>` - search stored items

## 1. Product Goal

Create a personal Telegram assistant that helps the user:

- capture thoughts, tasks, ideas, and agreements quickly via voice or text
- offload memory into a clear, structured system
- automatically parse and classify information
- plan the day and week with priorities
- act as both personal and work assistant in one tool

## 2. Core Workflow

1. User sends a voice note or text to Telegram.
2. Assistant:
   - understands the meaning
   - extracts key items (tasks, ideas, events, decisions, etc.)
   - saves them to a personal knowledge base
3. Assistant replies:
   - confirms the capture
   - summarizes what it understood
   - asks clarifying questions if needed
4. Later, the user can:
   - query the past
   - request plans
   - receive summaries and reminders

## 3. Supported Information Types

### 3.1 Tasks
- actions to be done
- with or without deadline
- priority and urgency
- work or personal

Example: "Call the window contractor tomorrow morning."

### 3.2 Events and Agreements
- meetings
- scheduled actions
- agreements with people

Example: "Meeting with the contractor on Friday about the house."

### 3.3 Notes / Memory Items
- facts
- reflections
- conclusions
- context for later use

Example: "Living room window leaks, possibly a thermal bridge."

### 3.4 Ideas
- business ideas
- product ideas
- "someday" thoughts

Example: "Build a landing page for Whirr Crew with a pricing calculator."

### 3.5 Decisions
- recorded decisions
- what and why

Example: "We decided to do drainage in spring, not now."

### 3.6 Contacts (Optional)
- important people
- relation or context
- why they matter

## 4. Context and Classification

The assistant should infer:
- context: work, personal, home, health, projects
- related project (if any)
- importance and urgency

If uncertain, the assistant must ask instead of guessing.

## 5. Voice Message Handling

The assistant must:
- accept short and long voice notes
- understand free-form speech
- produce:
  - a short summary
  - multiple extracted items

Example: a 10-minute monologue -> 1 summary + 3 tasks + 1 idea + 2 questions.

## 6. Response Behavior

### 6.1 Confirmation

After each input, the assistant should:
- confirm capture
- show what was created (e.g., "1 task, 1 note")

### 6.2 Clarifying Questions

If details are missing, the assistant should ask short, clear questions,
preferably with answer buttons:
- deadline?
- work or personal?
- urgency?

## 7. Queries and Analytics

The user can ask questions like:
- "What is important today?"
- "Show all open home tasks."
- "What did we agree on for project X?"
- "What ideas did I record last month?"

The assistant should search across all stored data and answer in a structured
format.

## 8. Planning

### 8.1 Daily Plan
- compile tasks for today
- sort by priority
- split into work and personal

### 8.2 Weekly Plan
- list key tasks and events
- highlight critical items

## 9. Tone and Style

The assistant should be:
- friendly, calm, and clear
- concise and to the point
- not technical
- feel like a personal assistant, not a "bot"

## 10. Future Integrations (Post-MVP)

- sync with note systems (Obsidian / Notion / Nuclino)
- export notes and tasks
- calendar and reminders integration

## 11. Data Model (MVP)

### 11.1 Common Fields

- id
- type: task | event | note | idea | decision | contact
- text: raw user text
- summary: assistant short summary
- context: work | personal | home | health | project | other
- project: optional project name
- priority: low | medium | high | critical
- urgency: low | medium | high
- due_at: optional datetime
- created_at
- source: text | voice
- references: people, places, related items

### 11.2 Example Item (Task)

```
type: task
summary: Call the window contractor
context: home
priority: medium
urgency: high
due_at: tomorrow morning
```

## 12. Processing Pipeline (MVP)

1. Telegram webhook receives message.
2. If voice:
   - speech-to-text (STT)
3. NLP extraction:
   - summarize
   - detect item types
   - extract dates, people, context, project, priority
4. Store items + raw text + metadata.
5. Generate response:
   - confirmation + summary + clarifying questions

## 13. Example Interaction

**User**: "Tomorrow morning call the window contractor. Also, living room
window leaks."

**Assistant**:

- "Captured: 1 task, 1 note."
- Task: "Call the window contractor" (context: home, due: tomorrow morning)
- Note: "Living room window leaks"
- "Is the task high priority?"

## 14. MVP Scope

Must have:
- Telegram bot (text + voice)
- multi-item extraction
- clarification flow
- searchable knowledge base
- daily and weekly plan output

Nice to have (post-MVP):
- calendar integration
- reminders
- external note sync

## 15. Non-Functional Requirements

- privacy-first storage
- fast response for short messages (< 3 sec)
- resilient to long voice notes
- minimal, human-friendly messages

## 16. Open Questions

- How are reminders delivered (Telegram messages vs. calendar)?
- Do we need explicit user-defined projects and tags?
- Preferred time zone handling for date parsing?
