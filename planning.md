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
<!-- Describe what this tool does in 1–2 sentences -->
search_listings will find the clothes that most fit the given characteristics of the desired clothes description, size, and max price. 
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): This parameter is the overall description of the requested item. 
- `size` (str): This parameter is the size that is extracted from the description. This parameter will be parsed by the LLM.
- `max_price` (float): This parameter is the size that is extracted from the description. This parameter will also be parsed by the LLM.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
This tool will return an empty list if there seems to be no clothes that match the characteristics. If there are clothes that exist in the mock dataset that match the user's description, the top listings of the clothes, which are sorted based on highest score, will be returned.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If the agent observes that there are no listings that match, the agent will stop looping on the task and will return a message to the user, letting it know that the requested item could not be found. Though this doesn't seem like it's implemented on the client-facing side so this will be implemented more in detail (i'll come with something later)
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

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

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

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
