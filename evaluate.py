"""
Milestone 6: Run the 5 evaluation questions end-to-end and dump everything
needed for the README (system answer, sources, and the retrieved chunks with
their distance scores).

    python evaluate.py
"""
from query import ask

QUESTIONS = [
    "What do students say about Dell Jensen's organic chemistry lectures and teaching?",
    "According to YikYak, which professor should I take for Organic Chemistry II, and why?",
    "Is Paul Croll's class hard, and what's his reputation?",
    "What are the main complaints about Ruby Auf's PUBH-300 (Epidemiology) class?",
    "On YikYak, which calculus (Math 160) professor is recommended for an easy class, and who should be avoided?",
]

for n, q in enumerate(QUESTIONS, 1):
    print("\n" + "#" * 78)
    print(f"# Q{n}: {q}")
    print("#" * 78)
    result = ask(q, k=4)

    print("\nSYSTEM ANSWER:")
    print(result["answer"])

    print("\nSOURCES: " + (", ".join(result["sources"]) or "(none — refused)"))

    print("\nRETRIEVED CHUNKS (top-4, with cosine distance):")
    for i, c in enumerate(result["chunks"], 1):
        snippet = c["text"][:200].replace("\n", " ")
        print(f"  [{i}] {c['source']}  dist={c['distance']:.3f}")
        print(f"      {snippet}...")
