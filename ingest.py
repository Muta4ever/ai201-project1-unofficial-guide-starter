import os

def chunk_text(text, source_name, chunk_size=500, overlap=100):
    """
    Splits text into fixed character chunks with a sliding window overlap.
    Attaches source metadata and filters out empty strings.
    """
    chunks = []
    start = 0

    # Clean up any residual whitespace blocks
    text = " ".join(text.split())

    while start < len(text):
        end = start + chunk_size
        chunk_content = text[start:end].strip()

        # Only keep substantive chunks (Filters out empty strings/fragments)
        if len(chunk_content) > 0:
            chunks.append({
                "text": chunk_content,
                "source": source_name,
                "length": len(chunk_content)
            })

        start += (chunk_size - overlap)

        if start >= len(text) - overlap:
            break

    return chunks

def load_all_chunks(docs_dir="./documents", verbose=False):
    """Load every .txt file, chunk it, and return one flat list of chunk dicts."""
    all_chunks = []

    if not os.path.exists(docs_dir):
        print(f"Error: '{docs_dir}' directory not found.")
        return all_chunks

    for filename in sorted(os.listdir(docs_dir)):
        if filename.endswith(".txt"):
            file_path = os.path.join(docs_dir, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read().lstrip("﻿")

            # Slice text into chunks with metadata attached
            file_chunks = chunk_text(raw_content, source_name=filename)
            all_chunks.extend(file_chunks)

            if verbose:
                print(f"Loaded {filename} -> Generated {len(file_chunks)} chunks.")

    return all_chunks

def run_ingestion_pipeline():
    print("=== Launching CodePath Ingestion Pipeline ===")

    all_chunks = load_all_chunks(verbose=True)

    print("\n" + "="*40)
    print("MILESTONE 3 DIAGNOSTIC CHECKPOINT")
    print("="*40)

    # 3. Rubric Count Verification
    total_chunks = len(all_chunks)
    print(f"TOTAL CHUNKS GENERATED: {total_chunks}")
    if total_chunks < 50:
        print("Warning: Fewer than 50 total chunks. Your chunks might be too large.")
    elif total_chunks > 2000:
        print("Warning: More than 2000 total chunks. Your chunks might be too small.")
    else:
        print("Success: Total chunk volume is within the healthy production zone.")

    print("\n--- Inspecting 5 Representative Chunks ---")

    # 4. Extract 5 evenly spaced chunks across your data to inspect standalone meaning
    sample_indices = [0, total_chunks//4, total_chunks//2, (3*total_chunks)//4, total_chunks-1]

    for rank, idx in enumerate(sample_indices, 1):
        if idx < total_chunks:
            chunk = all_chunks[idx]
            print(f"\n[Representative Chunk #{rank}] | Source: {chunk['source']} | Length: {chunk['length']} chars")
            print(f"Content: \"{chunk['text']}\"")
            print("-" * 30)

if __name__ == "__main__":
    run_ingestion_pipeline()
