

def chunk_text(text, chunk_size:int = 5000):

    text = text.replace("\n", " ").replace("\r", " ")

    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    return chunks

if __name__ == "__main__":
    import os
    from pathlib import Path

    file_path = Path("./test_chapters/chapter 2.txt")

    with open(file_path,"r") as f:
        content = f.read()

        chunks = chunk_text(content, chunk_size=5000)

        print(f"Total chunks: {len(chunks)}")

        for i, chunk in enumerate(chunks,start=1):
            print(f"Chunk {i}: {len(chunk)} characters")
            print(chunk)