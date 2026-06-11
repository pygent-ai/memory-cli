Use the memory-cli skill to answer the question below.

{{QUESTION}}

Return only one JSON object. Do not write files. Do not output Markdown. Do not output any explanatory text outside the JSON object.

JSON schema:

```json
{
  "answer": "...",
  "search_queries_and_cli_results": [
    {
      "query": "the exact query string you passed to memory-cli search",
      "cli_result_summary": "brief summary of the CLI result"
    }
  ],
  "notes": "..."
}
```

Hard constraints:
- Answer only from the memory-cli memory project in the current directory.
- Use the `memory-cli` command from the current directory's `.venv`.
- Call `memory-cli search` at least once.
- `search_queries_and_cli_results` must be an array of objects. Each object must contain `query` and `cli_result_summary`.
- `query` must exactly record the query string passed to `memory-cli search` so the answer can be audited later.
- Do not use outside knowledge to fill in answer-bearing details that are absent from retrieved memories.

Search strategy:
- Start with the user's wording, then search again with key entities, aliases, categories, and answer-type terms.
- For follow-up questions such as "remind me", "previous conversation", or "you mentioned", search for the specific detail being requested: website, link, number, list item, method, title, dish, app, material, sealant, chord progression, event, or named entity.
- For count, ordering, date, or time-window questions, search for each relevant entity and action separately. Gather all candidate memories before answering.
- If a retrieved memory is relevant but too broad, run narrower follow-up searches using exact names or phrases from that memory.

Answering strategy:
- If search retrieves the relevant conversation/session, do not abstain merely because the memory does not repeat the question wording exactly. Extract the answer-bearing detail from the retrieved content.
- For preference-style questions, the memory does not need to contain the exact current request. Transfer the user's remembered preferences into a useful answer when the domain is compatible. For example, hotel, event, food, product, travel, health, or lifestyle advice should reflect the user's stored preferences instead of defaulting to "I don't know" just because no current listing is stored.
- For follow-up/reminder questions, prioritize exact answer-bearing details over broad summaries. The final answer should usually be a concise name, title, link, number, method, item, or phrase when the question asks for one.
- For count questions, list candidate items internally, decide which are included or excluded, and answer with the final count. Pay close attention to wording such as "before X"; do not include X itself unless the question asks for it.
- For entity conflicts, be strict. If the question asks about one entity but memory clearly describes a different entity, do not reuse the different entity as the factual answer. However, for preference-style advice, compatible past preferences may still be used as guidance.
- If the memory supports a semantically equivalent answer with different wording, answer it directly rather than trying to match an exact reference phrase.

Before answering "I don't know":
- Confirm you searched the question's original wording.
- Confirm you searched key entities, likely aliases, and answer-type terms.
- Confirm you inspected all relevant returned matches, not just the first one.
- For follow-up questions, confirm you searched for the specific requested detail type.
- In `notes`, state exactly which answer-bearing detail is missing or which entity conflict prevents an answer.

`notes` requirements:
- Name the retrieved memory or session evidence used for the answer.
- Mention any entity conflict or uncertainty.
- For count questions, briefly state included and excluded items.
- If answering "I don't know", state the missing detail that prevents an answer.
