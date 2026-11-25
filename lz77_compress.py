import json
import sys

WINDOW = 100
MAX_MATCH = 255

def compress(text):
    result = []
    i = 0

    while i < len(text):
        best_length = 0
        best_distance = 0
        start = max(0, i - WINDOW)

        for j in range(start, i):
            length = 0
            while (length < MAX_MATCH and
                   i + length < len(text) and
                   text[j + length] == text[i + length]):
                length += 1

            if length > best_length:
                best_length = length
                best_distance = i - j

        next_char = text[i + best_length] if i + best_length < len(text) else ""
        result.append([best_distance, best_length, next_char])
        i += best_length + (1 if next_char else 0)

    return result

if len(sys.argv) != 3:
    print("Использование: python lz77_compress.py input.txt archive.json")
    raise SystemExit

with open(sys.argv[1], "r", encoding="utf-8") as f:
    text = f.read()

data = compress(text)

with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print("Архивация завершена.")
print("Исходный размер:", len(text.encode("utf-8")), "байт")
print("Размер архива:", os.path.getsize(sys.argv[2]), "байт")
