# Memory Extraction Guide

Use this reference when turning conversations, documents, project history, news, notes, or other source material into durable memory records.

## Extraction Principle

Do not preserve only summaries. Actively extract index-like facts that can answer natural-language questions.

Many future queries are not asking "what was this about?" They ask where an entity first appeared, when something happened, who or what is related, what category a concept belongs to, how a decision changed over time, or which aliases a user might use. A good memory should make those answers retrievable.

## What To Extract

### Entities

Capture named and important unnamed entities: people, organizations, places, works, products, projects, concepts, objects, events, decisions, files, systems, and features.

### Aliases And Query Terms

Record names a future user or agent might search for:

- abbreviations, short names, old names, foreign-language names, common labels, spelling variants, synonyms, and related keywords
- natural-language phrasings such as "when did X appear", "where was X first mentioned", "what is X related to", or "what is the current status of X"

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

## Retrieval Test Queries

Every important memory should include multiple realistic queries. Cover both exact terms and natural paraphrases. Useful patterns include:

- "when did X appear"
- "where was X first mentioned"
- "what is the relationship between X and Y"
- "when did X happen"
- "what is the latest status of X"
- "which organization/category/event does X belong to"
- "what was X called before"
- "what keywords should find X"

Queries should reflect how a future agent is likely to ask, not only how the source material phrased the fact.

## Review Checklist

Before adding or updating a memory, check:

- Does the memory identify the key entities?
- Does it include aliases or likely query terms?
- Does it preserve time, place, or source location when available?
- Does it state relationships explicitly?
- Does it capture state changes when the source contains a timeline?
- Can the content directly answer realistic natural-language questions?
- Do the retrieval tests include several paraphrases, including "when", "where", "who/what relationship", "current status", and category queries when relevant?

