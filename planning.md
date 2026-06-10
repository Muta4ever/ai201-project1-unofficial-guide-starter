# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? --> 

I chose Professor/Course Reviews as my project topic. During course registration, many students struggle to find professors and courses that best fit their learning preferences and academic goals. I selected this problem because the university currently only provides a course catalog, which offers limited information beyond basic course details. By the end of this project, I hope to create a system that provides more nuanced insights into professors and courses, allowing students to make more informed decisions when selecting classes and instructors.  
## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| #  | Source | Description | URL or location |
|----|--------|-------------|-----------------|
| 1  | Rate My Professors | Ashley Burge (English / FYI) — heavily negative, polarizing reviews | `documents/rmf_ashley_burge.txt` |
| 2  | Rate My Professors | Caglar Cetin (Sociology) — mostly positive, some "fixed in beliefs" critiques | `documents/rmf_caglar_cetin.txt` |
| 3  | Rate My Professors | Dell Jensen (Chemistry / Organic) — low rated, "teach yourself" complaints | `documents/rmf_dell_jensen.txt` |
| 4  | Rate My Professors | Diane Mueller (CS / Math) — highly rated, lots of homework | `documents/rmf_diane_mueller.txt` |
| 5  | Rate My Professors | Paul Croll (Sociology) — highly rated, funny, easy A | `documents/rmf_paul_croll.txt` |
| 6  | Rate My Professors | Ruby Auf (Public Health) — polarizing, disorganization complaints | `documents/rmf_ruby_auf.txt` |
| 7  | YikYak | Organic Chemistry II — "which professor to take?" thread | `documents/yikyak_chemistry_course.txt` |
| 8  | YikYak | Computer Science professors overview thread | `documents/yikyak_computer_science_reviews.txt` |
| 9  | YikYak | Calculus (Math 160) — lenient professor recommendations | `documents/yikyak_math_course_lore.txt` |
| 10 | YikYak | Dr. Auf epidemiology / public health experience thread | `documents/yikyak_public_health.txt` |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:** 500

**Overlap:** 100

**Reasoning:** My documents are short, opinion-dense reviews rather than long-form guides. I chose a fixed-size sliding-window chunker: take 500 characters at a time, then step forward by 400 (so each window overlaps the previous one by 100 characters). Before chunking, I strip the UTF-8 BOM and collapse all whitespace/newlines to single spaces so the source line breaks don't fragment the text.


## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers`
**Vector Store** ChromaDB cosine
**Top-k:** 4 

**Production tradeoff reflection:**
Accuracy on domain text: MiniLM is small and general-purpose. A larger model (all-mpnet-base-v2, or an API model like OpenAI text-embedding-3-large) would better separate near-duplicate sentiments like "disorganized but caring" vs "disorganized and mean."
Context length: MiniLM truncates ~256 tokens — fine for short reviews, but a longer-context model would matter for long guides/syllabi.
Multilingual: all docs are English now; I'd switch to a multilingual model if I added international-student forums.
Local vs API: local MiniLM is free with no rate limits, ideal here. In production I'd weigh an API model's better accuracy against per-call cost, latency, and the privacy of sending student data to a vendor.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Dell Jensen's organic chemistry lectures and teaching? | Strongly negative on teaching: smart/intelligent but can't teach well; lectures are confusing/boring; students must teach themselves; office hours help but don't fix it. (~19% would take again.) |
| 2 | According to YikYak, which professor should I take for Organic Chemistry II, and why? | **Boquin** — rated 10/10 because "he actually teaches." Jensen is mentioned only as a source of old exams/quizzes, not for teaching quality. |
| 3 | Is Paul Croll's class hard, and what's his reputation? | No, low difficulty (~2.1/5) and very high quality (~4.7/5, 95% would take again). Funny, caring, engaging, easy A; one critique that it can be too basic / politically polarized discussion. |
| 4 | What are the main complaints about Ruby Auf's PUBH-300 (Epidemiology) class? | Disorganization: syllabus/rubrics change repeatedly, instructions given only verbally, unclear deadlines; some students feel talked over. (Reviews are polarized — others praise her feedback and care.) |
| 5 | On YikYak, which calculus (Math 160) professor is recommended for an easy/lenient class, and who should be avoided? | Recommended: **Randazzo** (but "you have to lock in") and **Ben Civiletti** (one student finished with an A). Avoid: **Sward Andrews**. Mixed feelings on Civiletti ("acts like you're stupid"). |
---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. **Inconsistent / noisy formatting.** The RMP files aren't uniform — some are
   one-review-per-block separated by `---` (Jensen, Croll, Cetin, Auf), while Burge and Mueller are
   pre-summarized bullet lists. The chunker has to handle both layouts without producing fragments
   or merging multiple bullets into one diluted chunk.

2. Thin coverage → off-topic retrieval. Some topics (e.g. Math 160) live in only one short thread. When few relevant chunks exist, the top-k fills with loosely-related chunks from other professors, which can mislead the answer and pollute the source citations.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
```
 1. Ingestion        2. Chunking        3. Embedding + Store      4. Retrieval        5. Generation
 ------------        -----------        --------------------      ------------        -------------
 Load 10 .txt        Fixed-size         all-MiniLM-L6-v2          Embed query,        Groq
 files, strip   -->  sliding window --> (sentence-          -->   ChromaDB       -->  llama-3.3-70b
 BOM, collapse       500 chars,         transformers) ->          cosine search,      answers ONLY from
 whitespace          step 400           vectors in ChromaDB       top-k = 4           retrieved chunks
                     (100 overlap)      + metadata (source,                           + cites sources
                                        position, length)                                   |
                                                                                            v
                                                                                     Gradio web UI
                                                                                  (question -> answer
                                                                                     + source list)
```
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
IGive the AI my Documents + Chunking Strategy sections and a peer's chunk_text() and ask it to verify the fixed-size 500/100 splitter fits my review data and produces a healthy chunk count. Expect: a chunk count and inspection of sample chunks. Verify by reading 5 random chunks for fragments/HTML/empty strings.

**Milestone 4 — Embedding and retrieval:**
Give the AI my Retrieval Approach section and ask it to embed chunks with MiniLM, store them in ChromaDB with source metadata, and write retrieve(query, k=4). Verify by running 3 eval queries and checking the top chunks are on-topic with distances below 0.5.

**Milestone 5 — Generation and interface:**
Give the AI my grounding requirement (answer only from retrieved chunks; refuse otherwise) and desired output (answer + source list), plus the Gradio skeleton. Verify the system prompt actually enforces grounding and that an out-of-scope question is refused.
