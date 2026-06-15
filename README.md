# FitFindr

FitFindr is an AI-powered secondhand fashion assistant that takes a single natural language query, searches thrift listings for matching items, generates an outfit suggestion, and produces a social-media-ready fit card all in one automated agent loop.

## Setup

```bash
pip install -r requirements.txt
```

Add your Groq API key to a `.env` file (free key at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

Run the Gradio UI:

```bash
python app.py   # opens at localhost:7860
```

---

## Tool Inventory

### Tool 1: `search_listings(description, size, max_price)`

**Purpose:** Scores every listing in `data/listings.json` by keyword overlap with the user's description, filters by optional size and price, and returns the matches ranked by relevance.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `description` | `str` | Freeform keywords (e.g. `"vintage graphic tee"`). Tokenized on whitespace, matched case-insensitively against listing text fields. |
| `size` | `str \| None` | Case-insensitive substring match against the listing's size field (`"M"` matches `"S/M"`). Pass `None` to skip size filtering. |
| `max_price` | `float \| None` | Inclusive upper bound on price. Pass `None` to skip price filtering. |

**Returns:** A list of listing dicts sorted by relevance score descending. Each dict contains: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, `platform`. Listings with a score of 0 are excluded. Returns `[]` when nothing matches, and doesn't raise an exception

---

### Tool 2: `suggest_outfit(new_item, wardrobe)`

**Purpose:** Calls the Groq LLM to generate outfit ideas that pair the selected thrift listing with the user's wardrobe. Uses a different prompt depending on whether the wardrobe is empty.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `new_item` | `dict` | The top-ranked listing dict from `search_listings`. |
| `wardrobe` | `dict` | A dict with an `'items'` key containing a list of wardrobe item dicts (`name`, `category`, `colors`, `style_tags`). May be empty. |

**Returns:** A raw string from the LLM (`response.choices[0].message.content`) that contains one or two outfit suggestions. With an empty wardrobe: general styling ideas for the item (types of bottoms, shoes, overall vibe). With wardrobe items present: specific combinations that name wardrobe pieces by name.

---

### Tool 3: `create_fit_card(outfit, new_item)`

**Purpose:** Calls the Groq LLM to produce a 2–4 sentence OOTD-style social media caption. Guards against empty outfit input before making any API call.

**Inputs:**

| Parameter | Type | Description |
|---|---|---|
| `outfit` | `str` | The outfit suggestion returned by `suggest_outfit`. If empty or whitespace-only, the tool returns a descriptive error string immediately without calling the LLM. |
| `new_item` | `dict` | The top listing dict from `search_listings`. Used to extract `title`, `price`, and `platform` for the caption. |

**Returns:** A raw string from the LLM, which has a 2–4 sentence caption that mentions the item name, price, and platform once each, captures the outfit vibe, and reads like an authentic OOTD post. On empty/whitespace `outfit` input: returns a descriptive error string instead of raising an exception.

---

## Planning Loop

The agent runs a **fixed sequential pipeline**. Tool order is always the same; there is no dynamic replanning.

### Step-by-step:

1. **`_parse_query(query)`** Uses regex to extract `description`, `size`, and `max_price` from the raw user string. No LLM call. Stores result in `session["parsed"]`.

2. **`search_listings(description, size, max_price)`** - Runs keyword scoring over all 40 listings.
   - **Early exit (no results):** If the returned list is `[]`, `run_agent` writes a user-facing message to `session["error"]` and returns immediately. `suggest_outfit` and `create_fit_card` are **never called**.
   - **On results:** The top-ranked listing is stored in `session["selected_item"]`.

3. **`suggest_outfit(selected_item, wardrobe)`** - Always reached if search returned results. Stores the LLM response in `session["outfit_suggestion"]`.

4. **`create_fit_card(outfit_suggestion, selected_item)`** - Called inside a retry loop capped at **20 attempts**. On success the result is stored in `session["fit_card"]` and the loop exits.
   - **Early exit (retries exhausted):** If all 20 attempts raise an exception, `session["error"]` is set and `run_agent` returns early.

### Early-exit summary:

| Trigger | Condition | Effect |
|---|---|---|
| `search_listings` returns `[]` | No listings match the query | `session["error"]` set; loop ends before `suggest_outfit` |
| `create_fit_card` fails 20 times | LLM raises exception on every retry | `session["error"]` set; loop ends with incomplete session |

---

## State Management

State is a single Python dict initialized by `_new_session()` at the start of every `run_agent` call. It is the single source of truth for the entire loop. No tool receives the session dict directly. `run_agent` reads values out and passes them as explicit arguments, then writes each tool's output back before calling the next tool.

### Session fields and lifecycle:

| Field | Type | Set when | Read by |
|---|---|---|---|
| `query` | `str` | Initialization | `_parse_query` |
| `parsed` | `dict` | After `_parse_query` | `search_listings` call |
| `search_results` | `list` | After `search_listings` | Used to select `selected_item` |
| `selected_item` | `dict` | After search (index 0 of results) | `suggest_outfit`, `create_fit_card` |
| `wardrobe` | `dict` | Initialization | `suggest_outfit` |
| `outfit_suggestion` | `str` | After `suggest_outfit` | `create_fit_card` |
| `fit_card` | `str` | After `create_fit_card` | Caller (`app.py`) |
| `error` | `str \| None` | On early exit | Caller (`app.py`) |

The caller (`app.py`) checks `session["error"]` first. If it is `None`, all output fields (`search_results`, `outfit_suggestion`, `fit_card`) are populated and ready to display.

---

## Error Handling

### Per-tool failure modes:

| Tool / Layer | Failure Mode | Agent Response |
|---|---|---|
| `search_listings` | Returns `[]` when no listings match the query | `run_agent` sets `session["error"]` with a user-facing message ("No items found matching your search. Try different keywords, size, or price range.") and returns early. `suggest_outfit` and `create_fit_card` are never reached. |
| `suggest_outfit` | Wardrobe is empty (`wardrobe["items"] == []`) | Tool generates general styling advice via the LLM instead of outfit combinations. No exception is raised. The loop continues normally to `create_fit_card`. |
| `create_fit_card` | `outfit` argument is empty string or whitespace-only | Tool returns a descriptive error string immediately. The LLM is not called. No exception is raised. |
| `run_agent` (wrapping `create_fit_card`) | LLM call raises an exception | Retries up to 20 times. If all attempts fail, `session["error"]` is set to a message reporting the failure and `run_agent` returns early. |

### Concrete example from testing:

> - One specific failure that I triggered during testing is when that if a user tries to submit a cryptic query such as "xyzzy zzz ballgown under $1," the user will receive a message, "No items found matching your search. Try different keywords, size, or price range." The reason being is that our scoring algorithm in `search_listings` relies on keyword overlap, and a query with no meaningful keywords will fail to match any listings, resulting in an empty list `[]`. This triggers the early exit condition in `run_agent`, which sets `session["error"]` to the user-facing message and returns before reaching `suggest_outfit` or `create_fit_card`.

---

## Spec Reflection

>
> **Paragraph 1 - One way the spec helped:**
>
> A specific moment where having `planning.md` written in advance made development easier was when I was implementing the agent tools. The detailed tool signatures in `planning.md` provided clear guidance on the expected inputs and outputs for each tool, which helped ensure that the implementations aligned with the intended design. For instance, when implementing `suggest_outfit`, the spec's description of how the tool should behave with an empty wardrobe (generating general styling advice instead of specific combinations) prevented me from overlooking this edge case and ensured that the tool would function correctly regardless of the user's wardrobe state.



> **Paragraph 2 - One divergence from the spec and why:** 
> Upon implementing the plan, I found that implementing the query parsing logic using regex rather than an LLM call was more deterministic and straightforward for extracting structured parameters from the user's natural language query. The spec left the parsing approach open, and while I initially considered using an LLM for this step, I realized that regex would be more efficient and allow for the parsing behavior to be easily testable. This divergence from the spec allowed me to ensure that the `description`, `size`, and `max_price` parameters were consistently extracted in a structured format, which in turn improved the reliability of the subsequent `search_listings` tool call.

---

## AI Usage

### Instance 1 — Tool implementations (Milestone 3)

Claude Code was given the `### Tool 1–3` sections of `planning.md`, including parameter names, types, return value descriptions, and failure modes, plus the docstrings already present in `tools.py`, and was directed to implement `search_listings`, `suggest_outfit`, and `create_fit_card`. The generated implementations were run against the pre-written test suites in `tests/test_search_listings.py`, `tests/test_suggest_outfit.py`, and `tests/test_create_fit_card.py`. 

After Claude Code generated the implementations for the three tools one by one, I ran the corresponding test suites for each tool. For `search_listings`, all tests passed on the first attempt, which confirmed that the implementation correctly scored and filtered listings based on the provided parameters. However, for `suggest_outfit`, one of the tests failed because the generated outfit suggestions did not match the expected format in the test case. To address this, I reviewed the generated code and found that the prompt used for the LLM call was not specific enough about the desired output format. I revised the prompt to include clearer instructions on how to structure the outfit suggestions and regenerated the implementation. After this change, all tests for `suggest_outfit` passed successfully. For `create_fit_card`, there was a failure related to handling empty outfit input, which I resolved by adding an explicit check for empty or whitespace-only strings before making the LLM call, ensuring that it returned a descriptive error string as specified in the plan.


### Instance 2 — Planning loop (Milestone 4)

Claude Code was given the `## Planning Loop` and `## State Management` sections of `planning.md`, `agent-diagram.mmd` for the control-flow structure, and the `run_agent` docstring in `agent.py` for the step-by-step entry-point spec, and was directed to implement `run_agent` in `agent.py`. The generated implementation was run against `tests/test_agent.py`. Although Claude Code seemed to have implemented the sequential pipeline correctly, the initial implementation did not include the retry logic for `create_fit_card`. As a result, I manually added the retry loop around the `create_fit_card` call to ensure that the agent would attempt to generate a fit card up to 20 times in case of LLM exceptions, as specified in the plan. 
