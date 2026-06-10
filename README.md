# The Unofficial Guide — Project 1

A Retrieval-Augmented Generation (RAG) system that makes student-generated knowledge
about Augustana College professors searchable and answerable. Ask a plain-language
question and get a grounded, cited answer drawn from real student reviews.

## Demo Video

A 3–5 minute walkthrough of the system is included in this repo:
**[`walkthrough-2.mp4`](walkthrough-2.mp4)**. It shows multiple queries with source
citations, a query where retrieval works well, the Math 160 failure case, and a
walkthrough of the evaluation report.

---

## Domain

Student reviews of **professors and courses at Augustana College** — the unofficial opinions
students share about what a class is *actually* like: teaching quality, grading fairness,
how exams relate to lectures, organization, and which professor to pick when a course is
offered by several people.

This knowledge is valuable and hard to find through official channels because the course
catalog and department pages only tell you a course exists and who teaches it — they never
tell you that one organic chemistry professor expects you to teach yourself the entire course,
or that a sociology professor is an easy A but you won't learn much. That information only
lives in crowd-sourced reviews (Rate My Professors) and anonymous campus threads (YikYak),
scattered across hundreds of individual posts that nobody has ever summarized in one place.

---

## Document Sources

10 documents collected as `.txt` files in `documents/`. Two source types: **Rate My Professors
(RMP)** archives (many reviews per professor) and **YikYak** threads (short "who should I take?"
community Q&A). The mix gives both detailed individual reviews and quick community consensus,
and several professors appear in both source types so the system can corroborate or contrast them.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Ashley Burge (English / FYI) — heavily negative, polarizing | Rate My Professors | `documents/rmf_ashley_burge.txt` |
| 2 | Caglar Cetin (Sociology) — mostly positive | Rate My Professors | `documents/rmf_caglar_cetin.txt` |
| 3 | Dell Jensen (Chemistry / Organic) — low rated, "teach yourself" | Rate My Professors | `documents/rmf_dell_jensen.txt` |
| 4 | Diane Mueller (CS / Math) — highly rated, lots of homework | Rate My Professors | `documents/rmf_diane_mueller.txt` |
| 5 | Paul Croll (Sociology) — highly rated, funny, easy A | Rate My Professors | `documents/rmf_paul_croll.txt` |
| 6 | Ruby Auf (Public Health) — polarizing, disorganization complaints | Rate My Professors | `documents/rmf_ruby_auf.txt` |
| 7 | Organic Chemistry II — "which professor?" thread | YikYak | `documents/yikyak_chemistry_course.txt` |
| 8 | Computer Science professors overview | YikYak | `documents/yikyak_computer_science_reviews.txt` |
| 9 | Calculus (Math 160) — lenient professor recommendations | YikYak | `documents/yikyak_math_course_lore.txt` |
| 10 | Dr. Auf epidemiology / public health experience | YikYak | `documents/yikyak_public_health.txt` |

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 100 characters

**Preprocessing:** Each file is read with the UTF-8 BOM (`﻿`) stripped, and all internal
whitespace/newlines are collapsed to single spaces (`" ".join(text.split())`) before chunking,
so the raw line-break formatting of the source pages doesn't fragment the text.

**Why these choices fit your documents:** The corpus is review-heavy. A fixed-size 500-character
sliding window is simple and robust, and at 500 characters each chunk holds roughly one to two
short reviews' worth of opinion — enough standalone meaning for the embedding to carry signal.
The 100-character overlap is the important part: because a fixed-size cut doesn't respect review
or sentence boundaries, a thought that gets sliced at the boundary (e.g. "...he cannot teach to
save his" | "life...") reappears *whole* in the neighboring chunk, so retrieval can still recover
it. This is a deliberate simplicity-vs-precision tradeoff — a boundary-aware splitter on the `---`
separators would produce cleaner one-review chunks, but the fixed-size + overlap approach is far
less code and, with overlap, loses very little in practice. (See the Failure Case for where this
tradeoff bites.)

**Final chunk count:** 109 chunks across the 10 documents.

---

## Sample Chunks

Five representative chunks, each labeled with its source document. (Note: because chunking is
fixed-size, some chunks begin or end mid-review — this is the expected behavior of the
sliding-window strategy described above.)

**1 — `rmf_dell_jensen.txt`**
> PROFESSOR: Dell Jensen DEPARTMENT: Chemistry, Augustana College OVERALL QUALITY: 2.2 / 5 (Based on 24 ratings) WOULD TAKE AGAIN: 19% LEVEL OF DIFFICULTY: 4.3 / 5 RATING DISTRIBUTION: Awesome 5: 3 Great 4: 4 Good 3: 2 OK 2: 5 Awful 1: 11 --- QUALITY: 1.0 | DIFFICULTY: 5.0 COURSE: ORGANIC DATE: Jun 5th, 2026 ...

**2 — `rmf_paul_croll.txt`**
> PROFESSOR: Paul Croll DEPARTMENT: Sociology, Augustana College OVERALL QUALITY: 4.7 / 5 (Based on 30 ratings) WOULD TAKE AGAIN: 95% LEVEL OF DIFFICULTY: 2.1 / 5 ... QUALITY: 5.0 | DIFFICULTY: 1.0 COURSE: SOAN101 DATE: Mar 13th, 2026 ...

**3 — `rmf_ruby_auf.txt`**
> ...COURSE: PUBH-300 DATE: May 7th, 2026 For Credit: Yes | Attendance: Mandatory | Grade: B | Textbook: Yes I have not had a good experience in this class. The syllabus changed several times so I never knew what to expect. My grades did not reflect the effort I put in...

**4 — `yikyak_math_course_lore.txt`**
> --- SOURCE: YikYak Archive - Augustana Community TOPIC: Calculus (Math 160) POSTED: June 2026 POST: "I want to take Calculus (Math 160). I have already failed it once and I hate math. Which professor is the most relaxed, lenient, gives grades easily...? Choices: Brooke Randazzo, Ben Civiletti, Sward Andrews" ...

**5 — `rmf_diane_mueller.txt`**
> SOURCE: Rate My Professors Archive PROFESSOR: Diane Mueller (Computer Science / Mathematics) COURSE_FOCUS: CSC202 (Data Structures / Intro to Java) DATA: Overall Quality 4.7/5, Difficulty 3.3/5, 100% Would Take Again REVIEWS_SUMMARY: - Review (2023-02-03): Quality 5.0, Difficulty 3.0. Grade: A-. Amazing professor...

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim embeddings, runs locally,
no API key, no rate limits). Chunks are stored in a persistent **ChromaDB** collection configured
for **cosine** distance (`hnsw:space: cosine`). Retrieval returns the **top-4** chunks per query.

**Production tradeoff reflection:** If I were deploying this for real users and cost weren't a
constraint, I'd weigh:
- **Accuracy on domain-specific text:** MiniLM is small and general-purpose. A larger model
  (`all-mpnet-base-v2`, or an API model like OpenAI `text-embedding-3-large` or a Voyage model)
  would better separate near-duplicate review sentiments like "disorganized but caring" vs
  "disorganized and mean," which matters a lot for opinion text.
- **Context length:** MiniLM truncates around 256 tokens. My chunks are short so it's fine here,
  but for long-form guides or syllabi I'd want a longer-context embedding model.
- **Multilingual:** all docs are English now; if I added international-student forums I'd switch
  to a multilingual embedding model.
- **Local vs. API / latency:** local MiniLM has zero marginal cost and no rate limits, ideal for
  this project. In production with high traffic I'd weigh an API model's better accuracy against
  per-call cost, latency, and the privacy implications of sending student review data to a vendor.

---

## Retrieval Test Results

Top chunks retrieved for three evaluation queries (cosine distance — lower is closer):

**Query A: "What do students say about Dell Jensen's organic chemistry lectures?"**
| Rank | Source | Distance |
|---|---|---|
| 1 | rmf_dell_jensen.txt | 0.321 |
| 2 | rmf_dell_jensen.txt | 0.324 |
| 3 | rmf_dell_jensen.txt | 0.352 |
| 4 | yikyak_chemistry_course.txt | 0.370 |

*Why these are relevant:* Every chunk is about Jensen specifically. Ranks 1–3 are his RMP overview
and individual reviews about his teaching ("can't teach," "disorganized notes," "office hours
help"); rank 4 is the YikYak Organic Chem II thread that directly contrasts him with another
professor. All four distances are well below the 0.5 "good match" threshold.

**Query B: "Is Paul Croll's class hard, and what's his reputation?"**
| Rank | Source | Distance |
|---|---|---|
| 1 | rmf_paul_croll.txt | 0.336 |
| 2 | rmf_paul_croll.txt | 0.343 |
| 3 | rmf_paul_croll.txt | 0.417 |
| 4 | rmf_paul_croll.txt | 0.421 |

*Why these are relevant:* All four chunks come from Croll's RMP file and contain exactly the two
things the query asks about — difficulty (the 2.1/5 overview rating, "extremely straightforward")
and reputation ("absolutely AMAZING," "caring," "supportive"). No off-topic professors leaked in.

**Query C: "What are the main complaints about Ruby Auf's epidemiology class?"**
| Rank | Source | Distance |
|---|---|---|
| 1 | rmf_ruby_auf.txt | 0.459 |
| 2 | yikyak_public_health.txt | 0.463 |
| 3 | rmf_ruby_auf.txt | 0.468 |
| 4 | rmf_ruby_auf.txt | 0.468 |

Relevant: all four are Auf PUBH-300 content, and the retrieved chunks are predominantly the
critical reviews (unclear instructions, changing rubrics) that the query asks for.

---

## Grounded Generation

**System prompt grounding instruction:** The LLM (Groq `llama-3.3-70b-versatile`, temperature 0.1)
receives a system prompt that *enforces* grounding rather than suggesting it:

```
You are a helpful assistant that answers questions about professors and courses
using ONLY the provided context documents. Follow these rules strictly:
1. Use only information found in the context below. Do NOT use any outside or general knowledge.
2. If the context does not contain enough information to answer, reply exactly:
   "I don't have enough information on that."
3. Do not guess, speculate, or fill gaps with assumptions.
4. When reviews disagree, say so rather than presenting one side as the consensus.
```

The retrieved chunks are formatted into a numbered context block (`[Document 1 | source: ...]`)
and the question is only answered "using only the context above." Rule 2 was verified with an
out-of-scope question (see Example Responses) and the model reliably refuses.

**How source attribution is surfaced in the response:** Sources are **not** left to the LLM to
generate. After retrieval, the source filenames of the chunks that were actually retrieved are
collected programmatically (deduplicated, in rank order) and returned alongside the answer. If the
model returns the refusal string, the source list is suppressed (so a refused answer doesn't
display chunks it didn't use).

---

## Example Responses

**Example 1 — in-scope, with source attribution (`What do students say about Dell Jensen's
organic chemistry lectures and teaching?`):**
> Students have mixed opinions. Many describe his lectures as "overwhelming and hard to follow,"
> "confusing," and "disorganized," and say his notes are hard to follow for such a difficult class.
> One student praises him, saying he "truly cares for his students" and that office hours are
> helpful despite boring lectures. The YikYak thread advises taking Boquin instead, with one reply
> noting "Jensen doesn't [teach his class]" and that students rely on his old quizzes/exams.
>
> **Sources:** rmf_dell_jensen.txt, yikyak_chemistry_course.txt

**Example 2 — in-scope, with source attribution (`According to YikYak, which professor should I
take for Organic Chemistry II, and why?`):**
> You should take Professor Boquin. The reason given is "He can be strict, but you actually learn,"
> and it's implied he actively teaches his class, unlike Professor Jensen.
>
> **Sources:** yikyak_chemistry_course.txt, rmf_dell_jensen.txt

**Example 3 — out-of-scope refusal (`What is the best dining hall on campus?`):**
> I don't have enough information on that.
>
> **Sources:** *(none — the system declined to answer)*

---

## Query Interface

A **Gradio** web UI (`app.py`, run `python app.py` → http://localhost:7860).

- **Input field:** "Your question" — a textbox; submit with the **Ask** button or by pressing Enter.
- **Output fields:** "Answer" (the grounded response) and "Retrieved from" (the source documents,
  one per line; shows "(no sources — out of scope)" on a refusal).

**Sample interaction transcript:**
```
Your question:  Is Paul Croll's class hard, and what's his reputation?

Answer:         Paul Croll's class is not considered hard by most students — the overall
                difficulty is 2.1/5 and reviews call his classes "extremely straightforward."
                His reputation is excellent: 4.7/5 overall, 95% would take again, described as
                "absolutely AMAZING," "hilarious," "caring," and "inspirational."

Retrieved from: • rmf_paul_croll.txt
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Dell Jensen's organic chemistry lectures and teaching? | Smart but can't teach well; lectures confusing/overwhelming; students teach themselves; office hours help but don't fix it (~19% would take again). | Captured confusing/overwhelming/disorganized lectures, the lone positive (cares, office hours), and the "take Boquin instead" angle. | Relevant (all top-4 on Jensen) | Accurate |
| 2 | According to YikYak, which professor for Organic Chemistry II, and why? | Boquin — "you actually learn"; Jensen only cited as a source of old exams. | Correctly answered Boquin, "you actually learn," contrasted with Jensen. | Relevant | Accurate |
| 3 | Is Paul Croll's class hard, and what's his reputation? | Not hard (2.1/5); very highly rated (4.7/5, 95%); funny, caring, easy A. | Stated 2.1/5 difficulty, "straightforward," 4.7/5, 95%, praised reputation; noted one SOC321 review at 3.0. | Relevant (all top-4 on Croll) | Accurate |
| 4 | Main complaints about Ruby Auf's PUBH-300? | Disorganization: changing syllabus/rubrics, unclear/verbal instructions, dismissive of concerns. (Reviews are polarized.) | Listed unclear instructions, changing rubrics, poor attendance policy, dismissiveness, grades not matching effort; noted one positive counterpoint. | Relevant | Accurate |
| 5 | On YikYak, which Math 160 professor for an easy class, and who to avoid? | Recommend Randazzo ("lock in") and Civiletti (one got an A); avoid Andrews. | Said Randazzo recommended, avoid Andrews, Civiletti needs to "lock in." Mostly right, but **cited two irrelevant sources** and underweighted Civiletti's positive endorsement. | **Partially relevant** (only 1 of 4 chunks on-topic) | **Partially accurate** |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** Q5 — *"On YikYak, which calculus (Math 160) professor is recommended for
an easy class, and who should be avoided?"*

**What the system returned:** A mostly-correct answer (Randazzo recommended, avoid Andrews,
Civiletti needs effort), but with two problems: (a) the cited **sources included
`rmf_diane_mueller.txt` and `yikyak_chemistry_course.txt`**, neither of which is about Math 160 or
its professors, and (b) it framed Civiletti only as a caveat, underweighting the thread's strong
"Ben Civiletti for sure. Finished with an A" endorsement and omitting the "had to drop" warning.

**Root cause (tied to specific pipeline stages):** This is a **thin-coverage retrieval failure
compounded by naive source attribution**. Math 160 appears in only *one* short YikYak thread, which
chunks into just ~2 pieces. When the query is embedded, only the top result (distance 0.300) is
actually on-topic; ranks 2–4 (distances 0.511–0.513, all *above* the 0.5 threshold) are the nearest
*available* vectors — Diane Mueller's math reviews and the chemistry thread — because the corpus
simply doesn't contain four relevant chunks. Since source attribution is collected from **all k
retrieved chunks** rather than only the ones the model actually used, those off-topic filenames leak
into the citation list, making the answer look like it drew on Mueller and chemistry reviews when it
didn't.

**What you would change to fix it:** Two fixes, at two stages. (1) **Retrieval:** apply a distance
threshold (e.g. drop any chunk above ~0.5) so thin queries return fewer, on-topic chunks instead of
padding to k with noise. (2) **Attribution:** only cite sources whose chunks pass that threshold (or
have the LLM mark which documents it used), so the citation list reflects what actually grounded the
answer. A boundary-aware chunker would also help marginally by keeping the single Math 160 thread
intact instead of splitting it.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing the evaluation plan in `planning.md`
*before* coding meant I had five concrete, verifiable questions ready the moment retrieval worked.
That let me test retrieval against real target questions in Milestone 4 (and catch the cosine-vs-L2
distance issue immediately) instead of inventing test queries at the end. The anticipated-challenges
section also pre-warned me about polarized professors and thin coverage, so the Q5 failure was
something I recognized rather than something that blindsided me.

**One way your implementation diverged from the spec, and why:** The spec originally proposed a
boundary-aware chunker that splits on the `---` review separators (~400 chars, 50 overlap). I
diverged to a simpler **fixed-size 500/100 sliding window** because the code is much shorter and the
100-char overlap recovers most thoughts that get cut at a boundary. The tradeoff showed up honestly
in evaluation: it works well for professors with lots of reviews but produces some mid-word chunks
and contributed to the thin-coverage failure on Math 160 (documented above).

---

## AI Usage
**Instance 1 — Chunking pipeline review**
- *What I gave the AI:* My chunking strategy plus a peer's `chunk_text()` fixed-size sliding-window
  function, and asked whether it fit my review-style documents.
- *What it produced:* It ran the function on my corpus (109 chunks), pointed out that several sample
  chunks started mid-word (e.g. "mart person..." instead of "smart person") because fixed-size cuts
  ignore review boundaries, and flagged that the BOM character was leaking into the first chunk of
  each file.
- *What I changed or overrode:* I kept the fixed-size approach for simplicity (overriding the
  suggestion to switch to a boundary-aware splitter) but accepted the one-line BOM fix
  (`lstrip("﻿")`), and decided to document the mid-word fragments as a known tradeoff.

**Instance 2 — Embedding/retrieval and distance metric**
- *What I gave the AI:* My retrieval approach (all-MiniLM-L6-v2, ChromaDB, top-4) and asked it to
  build the embedding + retrieval module.
- *What it produced:* A working module, but the first run showed all distances at 0.6–0.9 — above
  the 0.5 "good match" threshold. It diagnosed that ChromaDB defaults to L2 distance while MiniLM
  embeddings are meant for cosine.
- *What I changed or overrode:* I had it set the collection to cosine distance
  (`metadata={"hnsw:space": "cosine"}`); distances dropped to 0.3–0.48 and the checkpoint passed.
  I also directed it to suppress the source list on refusals rather than showing irrelevant chunks.
```
