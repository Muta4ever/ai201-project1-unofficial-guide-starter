"""
Milestone 5: Grounded answer generation.

Retrieves the top-k chunks, sends ONLY those to the LLM as context, and returns
an answer plus the source documents the context came from. Sources are collected
programmatically from the retrieved chunks, not left to the LLM to invent.

    python query.py        # runs a few end-to-end test questions
"""
import os

from dotenv import load_dotenv
from groq import Groq

from embed import retrieve

load_dotenv()

LLM_MODEL = "llama-3.3-70b-versatile"
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about professors and "
    "courses using ONLY the provided context documents. "
    "Follow these rules strictly:\n"
    "1. Use only information found in the context below. Do NOT use any outside "
    "or general knowledge.\n"
    "2. If the context does not contain enough information to answer, reply "
    "exactly: \"I don't have enough information on that.\"\n"
    "3. Do not guess, speculate, or fill gaps with assumptions.\n"
    "4. When reviews disagree, say so rather than presenting one side as the "
    "consensus."
)


def _build_context(chunks):
    """Format retrieved chunks into a numbered context block for the prompt."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[Document {i} | source: {c['source']}]\n{c['text']}")
    return "\n\n".join(blocks)


def ask(question, k=4):
    """Return {'answer': str, 'sources': [str], 'chunks': [...]} for a question."""
    chunks = retrieve(question, k=k)
    context = _build_context(chunks)

    user_prompt = (
        f"Context documents:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above."
    )

    completion = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )
    answer = completion.choices[0].message.content.strip()

    # Source attribution is built from what was actually retrieved, in order,
    # deduplicated — never left to the model to produce. When the system refuses
    # (no grounding found), don't list sources for chunks it didn't actually use.
    if answer.lower().startswith("i don't have enough information"):
        sources = []
    else:
        sources = list(dict.fromkeys(c["source"] for c in chunks))

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    test_questions = [
        "What do students say about Dell Jensen's organic chemistry lectures?",
        "According to YikYak, which professor should I take for Organic Chemistry II?",
        "What is the best dining hall on campus?",  # out-of-scope -> should refuse
    ]

    for q in test_questions:
        print("\n" + "=" * 70)
        print(f"Q: {q}")
        print("=" * 70)
        result = ask(q)
        print(f"\nANSWER:\n{result['answer']}\n")
        print("SOURCES: " + ", ".join(result["sources"]))
