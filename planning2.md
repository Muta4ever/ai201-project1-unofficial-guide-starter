# Project 1 Planning: The Unofficial Guide

> ⚠️ This is a **sample / model** version of `planning.md`, filled in by going through
> the 10 documents in `documents/`. Read it to see what "substantive, not placeholder"
> looks like for Milestone 2, then rewrite the real `planning.md` in your own words.
> Don't submit AI-generated planning — the project explicitly warns against that. Use this
> to understand the shape of a good spec, then make the decisions yourself.

---

## Domain

I chose **student reviews of professors and courses at Augustana College**. Specifically, the
"unofficial" opinions students share about what a professor's class is *actually* like to take —
teaching quality, grading fairness, how exams relate to lectures, organization, and which
professor to pick when a course is taught by several people.

This knowledge is valuable and hard to find through official channels because the course catalog
and department pages only tell you a course exists and who teaches it — they never tell you that
one organic chemistry professor expects you to teach yourself the entire course, or that a
sociology professor is an easy A but you won't learn much. That information only lives in
crowd-sourced reviews (Rate My Professors) and anonymous campus threads (YikYak), and it's
scattered across hundreds of individual posts that nobody has ever summarized in one place.

---

## Documents

10 source documents, collected as `.txt` files in the `documents/` folder. Two source types:
**Rate My Professors (RMP) archives** (longer, many reviews per professor) and **YikYak threads**
(short, conversational Q&A about which professor to take). The mix gives both detailed individual
reviews and quick "who should I take?" community consensus.

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

**Coverage note:** the sources overlap intentionally — Auf appears in both an RMP file (#6) and a
YikYak thread (#10), and Jensen appears in both his RMP file (#3) and the chemistry YikYak thread
(#7). This lets the system corroborate (or contrast) the detailed review data against quick
community consensus.

---

## Chunking Strategy

**Chunk size:** ~400 characters (target), with a hard floor so tiny fragments get dropped/merged.

**Overlap:** 50 characters.

**Reasoning:**

These documents are **review-heavy, not long-form**. In the RMP files, each review is already a
self-contained unit: a metadata header (`QUALITY | DIFFICULTY | COURSE | DATE`) followed by 1–5
sentences of opinion, separated by `---`. A single review is exactly the "complete, retrievable
thought" the project asks for — e.g. *"Jensen is the worst professor I've ever had... he cannot
teach to save his life... expects you to learn everything yourself."* That stands on its own and
answers a query by itself.

So my primary strategy is **split on the natural review boundary** (`---` for RMP files, and
POST/REPLY structure for YikYak threads) rather than blindly cutting every N characters. Most
individual reviews land around 300–450 characters, which is why I set the target chunk size near
400 — it matches the natural unit instead of fighting it. When a single review is unusually long,
I fall back to a ~400-char split *with 50-char overlap* so a sentence that spans the cut is still
recoverable from either side.

- **Why not bigger (e.g. 500–1000)?** Bigger chunks would glue several unrelated reviews together.
  A query like "are Jensen's exams like the lectures?" would then match a blob that also discusses
  his office hours, his chalk, and a different course — diluting the embedding and the answer.
- **Why not smaller (e.g. 150)?** A 150-char chunk would chop a review mid-thought
  (*"Professor's exams are heavily"*) — a fragment with no standalone meaning, exactly the bad case
  the rubric warns about.
- **Overlap is small (50)** because the review boundary already keeps thoughts intact; I only need
  a little overlap to cover the rare cross-boundary sentence, not to stitch a long narrative.
- **Each chunk keeps its review header / source context** (professor name + course + date) attached
  via metadata so a retrieved chunk can be attributed without re-reading neighbors.

**How I'll know it's wrong:** if printed chunks are fragments or empty → too small / bad splitter.
If a single chunk covers two professors or three topics → too big, go back to per-review splitting.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` (runs locally, no API key,
384-dim embeddings). Vector store: **ChromaDB** (local, persistent).

**Top-k:** 4. Each chunk ≈ one review, and most of my test questions are about the *consensus*
across reviews ("what do students say about X"), so I want a few independent reviews, not one. 4 is
enough to surface a couple of corroborating opinions without pulling in loosely-related reviews
about a different course that would pull the LLM off-topic. I'll tune this after seeing real
distance scores in Milestone 4.

**Production tradeoff reflection (if cost weren't a constraint):**

- **Accuracy on domain-specific text:** `all-MiniLM-L6-v2` is small and general-purpose. A larger
  model (e.g. `all-mpnet-base-v2`, or an API model like OpenAI `text-embedding-3-large` /
  Voyage's domain models) would better distinguish near-duplicate review sentiments
  ("disorganized but caring" vs "disorganized and mean").
- **Context length:** MiniLM truncates around 256 tokens. My chunks are short so that's fine here,
  but for long-form guides I'd want a longer-context embedding model.
- **Multilingual:** all my docs are English, so multilingual support isn't needed now; if I added
  international-student forums I'd switch to a multilingual model.
- **Local vs API / latency:** local MiniLM has zero marginal cost and no rate limits, which is
  perfect for a free project. In production with high traffic I'd weigh an API model's better
  accuracy against per-call cost, latency, and sending student data to a third party (privacy).

**Why semantic search helps here:** a student might ask "is Jensen's class a lot of
self-teaching?" — no review uses the phrase "self-teaching," but reviews say "you have to teach
yourself everything." Semantic similarity matches the *meaning*, not the exact words, which
keyword search would miss.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Dell Jensen's organic chemistry lectures and teaching? | Strongly negative on teaching: smart/intelligent but can't teach well; lectures are confusing/boring; students must teach themselves; office hours help but don't fix it. (~19% would take again.) |
| 2 | According to YikYak, which professor should I take for Organic Chemistry II, and why? | **Boquin** — rated 10/10 because "he actually teaches." Jensen is mentioned only as a source of old exams/quizzes, not for teaching quality. |
| 3 | Is Paul Croll's class hard, and what's his reputation? | No, low difficulty (~2.1/5) and very high quality (~4.7/5, 95% would take again). Funny, caring, engaging, easy A; one critique that it can be too basic / politically polarized discussion. |
| 4 | What are the main complaints about Ruby Auf's PUBH-300 (Epidemiology) class? | Disorganization: syllabus/rubrics change repeatedly, instructions given only verbally, unclear deadlines; some students feel talked over. (Reviews are polarized — others praise her feedback and care.) |
| 5 | On YikYak, which calculus (Math 160) professor is recommended for an easy/lenient class, and who should be avoided? | Recommended: **Randazzo** (but "you have to lock in") and **Ben Civiletti** (one student finished with an A). Avoid: **Sward Andrews**. Mixed feelings on Civiletti ("acts like you're stupid"). |

All five have answers I can verify against specific lines in the documents, so a grader (or I) can
judge accurate / partially accurate / inaccurate.

---

## Anticipated Challenges

1. **Polarized professors → biased / one-sided answers.** Auf and Burge have both glowing 5.0 and
   scathing 1.0 reviews. If top-4 retrieval happens to pull only the negative (or only the positive)
   chunks, the generated answer will sound like a confident consensus when the reality is split.
   This is a retrieval-coverage problem, and a likely **failure case** to document — the answer
   isn't "wrong" per se, it's misleadingly one-sided. Mitigation: report it honestly; consider
   raising k or noting disagreement in the prompt.

2. **Conflicting sources across document types.** The CS YikYak thread says Mueller is "gone" and
   even "the anti-Christ," while her RMP file is overwhelmingly positive (4.7/5). The system could
   merge these into a contradictory or confusing answer, or cite the wrong source for a claim.
   Source attribution has to be exact so the user can see *which* source said what.

3. **(Bonus risk) Inconsistent / noisy formatting.** The RMP files aren't uniform — some are
   one-review-per-block separated by `---` (Jensen, Croll, Cetin, Auf), while Burge and Mueller are
   pre-summarized bullet lists. The chunker has to handle both layouts without producing fragments
   or merging multiple bullets into one diluted chunk.

---

## Architecture

```
 1. Ingestion        2. Chunking        3. Embedding + Store      4. Retrieval        5. Generation
 ------------        -----------        --------------------      ------------        -------------
 Load 10 .txt        Split on review    all-MiniLM-L6-v2          Embed query,        Groq
 files, strip   -->  (---) & POST/  --> (sentence-          -->   ChromaDB       -->  llama-3.3-70b
 BOM/headers,        REPLY, ~400        transformers) ->          similarity          answers ONLY from
 clean whitespace    chars, 50          vectors in ChromaDB       search,             retrieved chunks
                     overlap            + metadata (source,       top-k = 4           + cites source files
                                        professor, position)                                |
                                                                                            v
                                                                                     Gradio web UI
                                                                                  (question -> answer
                                                                                     + source list)
```

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:**
I'll give **Claude** my *Documents* table and *Chunking Strategy* section above (plus a note that RMP
reviews are separated by `---` and YikYak files use POST/REPLY structure) and ask it to implement
`load_documents()` and `chunk_text()` — splitting on the review boundary first, falling back to a
~400-char / 50-overlap split for long reviews, attaching `{source_file, professor, chunk_index}`
metadata, and dropping empty/whitespace chunks. **Verify:** print 5 random chunks and confirm each
is a complete, single-review thought with the right source attached; confirm total chunk count is
in the 50–2000 range the rubric expects (this corpus will likely land around 80–150 chunks).

**Milestone 4 — Embedding and retrieval:**
I'll give Claude the *Retrieval Approach* section and the architecture diagram and ask it to embed
all chunks with `all-MiniLM-L6-v2`, persist them to ChromaDB with metadata, and write
`retrieve(query, k=4)` returning chunks + source + distance scores. **Verify:** run test questions
1, 3, and 4, print returned chunks with distances, and confirm top results are on-topic with
distances below ~0.5 before adding any generation. If anything I don't recognize in the ChromaDB
API shows up, I'll ask Claude to explain it line by line.

**Milestone 5 — Generation and interface:**
I'll give Claude my grounding requirement (answer **only** from retrieved chunks; if they don't
cover it, say "I don't have enough information on that") and the desired output (answer + list of
source files), plus the Gradio skeleton from the instructions. I'll ask it to wire retrieval → Groq
`llama-3.3-70b-versatile` → response, appending source filenames **programmatically** rather than
trusting the model to cite. **Verify:** I'll read the system prompt to confirm grounding is
*enforced*, test an out-of-scope question (e.g. "what's the best dining hall?") to confirm it
refuses, and check that a normal answer's cited sources actually match the chunks that were
retrieved.
