# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
`search_listings` scores every listing in `data/listings.json` by keyword overlap with the user's description, then filters by optional size and max price. It returns the matching listings sorted by relevance score (highest first), or an empty list if nothing matches.

**Input parameters:**
- `description` (str): Freeform keywords describing the item (e.g. "vintage graphic tee"). Tokenized on whitespace and matched case-insensitively.
- `size` (str | None): Size to filter by. Matched as a case-insensitive substring of the listing's size field, so "M" matches "S/M" and "xl" matches "XL (oversized)". Pass `None` to skip size filtering.
- `max_price` (float | None): Maximum price (inclusive). Pass `None` to skip price filtering.

**What it returns:**
A list of listing dicts, each with fields: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, `platform`. Results are sorted by relevance score descending; listings with a score of 0 are excluded. Returns `[]` if nothing matches — never raises.

Scoring algorithm: tokenize `description` into a keyword set, then count how many tokens appear in any of a listing's text fields: `title`, `description`, `category`, `brand` (joined and split on whitespace) plus `style_tags` and `colors` (list values, lowercased). Score = number of matching unique tokens.

This scoring algorithm is simple and fast. However, this algorithm doesn't account for typos, semantic understanding, and unbroken ties. 

Since this is a project with a small, curated data set, this scoring algorithm is a good start. But as we scale, approaches like using BM25 for text ranking or embedded-based search should be considered. 


**What happens if it fails or returns nothing:**
If the returned list is empty, the agent stops the loop early and returns a message to the user saying no matching items were found. The tool itself never raises an exception and the agent loop is responsible for detecting the empty result.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
suggest_outfit will take in the new_item, an item that is the top-matching result from the list that has returned by search_listings, and a wardrobe. With those parameters, suggest_outfit will give a string-based outfit suggestion. 
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The top item from the result list of search_listings.  
- `wardrobe` (dict): The current wardrobe, which could be either empty upon a new user or the example wardrobe.

**What it returns:**
<!-- Describe the return value -->
suggest_outfit will return a string that represents the description of the outfits that are recommended, which will come from the response of the LLM.  
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the agent sees that the wardrobe is empty, it will offer general styling advice with the new_item. Ending the loop and treating an empty wardrobe as an error
is good in principle but seems slightly restricting.   
If the agent sees that no outfits can be suggested, we can set session error and return early.  
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
create_fit_card will take in the outfit suggested, which will be given from the suggest_outfit tool, and the new_item, which was the first item from the top listings given by search_listings. 
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The description of the suggested outfit given from the suggest_outfit tool.
- `new_item` (dict): The top item from the result list of search_listings.  
**What it returns:**
<!-- Describe the return value -->
create_fit_card will return a string of paragraph length that represents a Instagram/TikTok styled caption, which should give off an informal and authentic vibe similar to an (Outfit-Of-The-Day) type of post rather than a product description. Additionally, for everytime there is a different input, it should output a unique description that shouldn't be similar to previous ones.  
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
First, allow the agent to run about 20 iterations of the loop to make the caption. If it's the case that the agent fails to make a caption by then, the agent can then set the error message, and close the loop. 
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The underlying pattern at each stage in the planning loop is that it can only proceed to the next step if it's received the adequate information to call the next tool. For example, when we parse the user's query to extract a description, size, and max_price, and the wardrobe, the agent then asks if it has all of those parameters. Then, if so proceeds to call the first tool, search_listings(). At each step in the planning loop, it will mirror this ReAct loop until it has finished or it hits a session error at any point in the planning loop. For the definition of finished, if the agent has been able to finish calling create_fit_card(), the last tool cool, with the resulting session successfully storing the fit_card, this will indicate the end of the session for the agent and it will stop looping. 
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent stores the information at each session in a dictionary, which will serve as the single source of truth that the LLM will refer to throughout the loop. At the end of each tool call, the result that will be needed for the next tool call will be stored in that dictionary for the agent to refer to. Unless the necessary information for whichever tool call is stored in the dictionary, the agent may not proceed to the next tool call.  
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | The agent will return a message to the user, letting it know that the requested item could not be found. |
| suggest_outfit | Wardrobe is empty | Offer general styling advice with the new_item.  |
| create_fit_card | Outfit input is missing or incomplete | The agent will end and return the error message sent for that session |

---

## Architecture

Please refer to ``agent-diagram.mmd`` for the architecture diagram.
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**


          Claude Code will be used to produce the tool implementations. For context, it will receive the description of the tools implementation on ``planning.md`` and will look for "### Tool 1: search_listings". Then, it will read the ``agent-diagram.mmd`` file to get the high-level idea of each tools implementation and how they connect with each other. Additionally, it will receive the tools.py file for it to read the documentation of each tooling and the more minute details of how it should methodically write the code. The code expected to be produce are the toolings that properly align with how the tool's specs, diagram, and documentation reflected it to be. Additionally, the produced code should then be able to pass a pre-written test suite for each tooling.  
     

**Milestone 4 — Planning loop and state management:**

          Claude Code will be used to implement the agent loop and the state management. For context, it will receive ``planning.md`` and it will specifically look for the labels "## Planning Loop" and "## State Management". Then, it will read the ``agent-diagram.mmd`` file to understand the agents action at each step. Additionally, it will receive the agent.py file for it to read the documentation of the run_agent method and which was the more detailed explanation of the agent's entry point. The code expected to be produce should properly align with how the given specs, diagram, and documentation reflects the agents behaviors and procedures. Additionally, the produced code should then be able to pass a pre-written test suite for the agents functionality.  
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
First, the age will receive the user query as the description and parse any information on the size and cost of the item. In this case, the agent will look at the user query, see that they want a max price of "under $30". However, since no size is specified, it will be marked as None. Then, the agent will take the description and max_price as parameters to then call search_listings(). 


**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
So, if search_listings() returns an empty list (i.e, the agent couldn't find an item matching the user's query), then the agent will end the loop early and return a message to the user saying that it could not find an item matching its query. Otherwise, if search_listings() were to successfully a return a list with new_items, the 1st ranked new_item of that list, based on the highest score, will be written to the session state for the agent to refer to. 

**Step 3:**
<!-- Continue until the full interaction is complete -->
If that new_item exists in the session state, the agent will now call suggest_outfit() with parameters being the new_item from the session state and the user's wardrobe, which could be empty. If the wardrobe is empty, the agent itself will offer general styling advice without stopping the loop and proceed to the next step with the outfit written to the session state. If there is a wardrobe, the outfit will be made and also be written to the session state. 

Lastly, once the outfit is generated, the agent will now call the last tool, create_fit_card(), which will take in the outfit and the new_item from the session state. The agent will write the fit_card With specific instructions to write it in a OOTD fashion. If the agent fails to write the fit_card after 20 iterations, it will return with a session error that is displayed to the client.  

**Final output to user:**
<!-- What does the user actually see at the end? -->
Upon successfully generating the fit_card and storing it into the session state, the session will be marked as complete and the agent will end it's loop. The final output should include the information from the session state added into all of the designated client rows.  