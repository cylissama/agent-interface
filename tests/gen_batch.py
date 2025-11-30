import os

def main():
    paragraphs = [
        "Call me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse...",
        "It was the best of times, it was the worst of times, it was the age of wisdom, it was the age of foolishness...",
        "In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, filled with the ends of worms...",
        "All children, except one, grow up. They soon know that they will grow up, and the way Wendy knew was this...",
        "It is a truth universally acknowledged, that a single man in possession of a good fortune...",
        "The sun shone, having no alternative, on the nothing new. Murphy sat out of it...",
        "Far out in the uncharted backwaters of the unfashionable end of the western spiral arm of the Galaxy...",
        "There was no possibility of taking a walk that day. We had been wandering, indeed, in the leafless shrubbery...",
        "The sky above the port was the color of television, tuned to a dead channel...",
        "He was an old man who fished alone in a skiff in the Gulf Stream, and he had gone eighty-four days now without taking a fish..."
    ]

    folder = "batch"
    os.makedirs(folder, exist_ok=True)

    for i, para in enumerate(paragraphs, start=1):
        filename = os.path.join(folder, f"file_{i}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(para)

    print(f"Created {len(paragraphs)} files in '{folder}/'")

if __name__ == "__main__":
    main()
