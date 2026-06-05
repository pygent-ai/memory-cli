# Memory Extraction Guide

Use this reference when turning conversations, documents, project history, news, notes, or other source material into durable memory records.

## Extraction Principle

Do not preserve only summaries. Actively extract index-like facts that can be found by keyword and key-phrase retrieval tests.

Many future searches are not asking "what was this about?" They use entity names, aliases, categories, relationships, dates, locations, or status terms. A good memory should make those facts retrievable through concise keywords and key phrases.

## What To Extract

### Entities

Capture named and important unnamed entities: people, organizations, places, works, products, projects, concepts, objects, events, decisions, files, systems, and features.

### Aliases And Query Terms

Record names a future user or agent might search for:

- abbreviations, short names, old names, foreign-language names, common labels, spelling variants, synonyms, and related keywords
- concise key phrases for time, source location, relationships, categories, previous names, and current status

### Time And Location

Capture facts that anchor the memory:

- first appearance time, first mention, occurrence time, publication time, decision time, or update time
- source location such as chapter, page, file path, issue, PR, meeting, conversation, section, paragraph, or line number when available

### Relationships

Extract relationships between entities:

- person-to-person, person-to-organization, project ownership, product version lineage, concept category, event cause/effect, dependency, implementation choice, and historical phase

### State And Change

When the source describes movement over time, preserve the transition:

- previous state, later state, current state
- why the change happened and which source established the current rule

This is especially important for news, project decisions, historical processes, career history, product updates, and changing user preferences.

### Directly Answerable Facts

Each important memory should contain facts that directly answer likely questions, not just background context. Prefer precise statements such as:

- "X first appears in Y at Z."
- "X happened on DATE."
- "X belongs to CATEGORY."
- "X and Y are related by RELATIONSHIP."
- "X used to be OLD_STATE; after EVENT_OR_DECISION it became NEW_STATE."

### Answer-Bearing Details

Do not preserve only high-level summaries when the source contains details that a future user may ask for directly.

Preserve exact values such as numbers, dates, durations, prices, percentages, quantities, names, titles, URLs, handles, locations, ordered-list positions, versions, model names, and selected options.

Bad:

- "The user discussed a project planning tool."

Good:

- "The user selected Linear for project tracking on 2026-05-12 because they wanted lightweight issue triage, GitHub integration, and cycle planning."

### Lists And Enumerations

When the source contains a numbered list, recommendation list, comparison table, recipe, checklist, ranking, generated options, or resource list, preserve item-level details that may be queried later.

For important items, retain:

- position or label when present
- item name
- distinguishing attributes
- exact value, link, or decision when present

For long lists, preserve a compact index rather than collapsing the whole list into a topic summary.

### Transferable Preferences

When a source reveals a user preference inside a specific task, preserve both the task-specific decision and the reusable preference.

Good:

- "The user chose Option A for this purchase because it was compact and quiet."
- "The reusable preference is that the user tends to prefer compact, quiet tools for shared workspaces."

Do not store only the specific item when the reason should guide future similar choices.

### Timelines And Current Values

When a fact changes over time, preserve the previous value, the updated value, and which value is current. Include the date, event, or source that established the current value when available.

Good:

- "The user initially preferred Tool A for deployment automation. After the staging incident on 2026-04-18, they switched to Tool B; Tool B is the current preference."

## Retrieval Test Queries

Every important memory should include multiple keyword or key-phrase queries. Cover exact names, aliases, categories, relationships, and compact phrases that should retrieve the same memory. Useful patterns include:

- entity names and aliases
- source locations or first-mention phrases
- relationship phrases that combine two related entities
- event names plus dates or time periods
- current-status phrases
- category, organization, project, or feature labels
- previous names and renamed-state phrases

Queries should be short retrieval keys, not full prompts. Multiple queries may match the same memory, and a search may receive multiple keyword/key-phrase inputs that return separate result groups in input order.

For preference and reusable-context memories, include queries at multiple levels:

- source-context queries: terms from the original situation
- generalized queries: reusable preference or relationship language
- transfer-context queries: likely future situations where the memory should still apply

Example:

- Source context: "quiet mechanical keyboard for office"
- Generalized: "prefers quiet compact tools"
- Transfer context: "shared workspace equipment recommendation"

## Review Checklist

Before adding or updating a memory, check:

- Does the memory identify the key entities?
- Does it include aliases or likely query terms?
- Does it preserve time, place, or source location when available?
- Does it state relationships explicitly?
- Does it capture state changes when the source contains a timeline?
- Can the content directly answer facts implied by the keyword or key-phrase queries?
- Do the retrieval tests include several keywords or key phrases for entities, aliases, relationships, source locations, current status, and categories when relevant?
- Does it preserve exact answer-bearing details rather than only the topic?
- If the source contains a list or enumeration, does the memory preserve important item-level details?
- If the source contains a reusable preference, do the tests include source-context, generalized, and transfer-context queries?
- If the source changes an existing fact, is the current value explicit?
