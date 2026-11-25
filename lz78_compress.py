import json
import sys
import os

def compress(text):
    dictionary = {}
    result = []
    next_index = 1
    i = 0

    while i < len(text):
        phrase = ""
        prefix_index = 0
        j = i

        while j < len(text) and phrase + text[j] in dictionary:
            phrase += text[j]
            prefix_index = dictionary[phrase]
            j += 1

        if j < len(text):
            new_char = text[j]
            result.append([prefix_index, new_char])
            dictionary[phrase + new_char] = next_index
            next_index += 1
            i = j + 1
        else:
            result.append([prefix_index, ""])
            i = len(text)

    return result

if len(sys.argv) != 3:
    print("Использование: python lz78_compress.py input.txt archive.json")
    raise SystemExit

with open(sys.argv[1], "r", encoding="utf-8") as f:
    text = f.read()

data = compress(text)

with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print("Архивация завершена.")
print("Исходный размер:", len(text.encode("utf-8")), "байт")
print("Размер архива:", os.path.getsize(sys.argv[2]), "байт")
