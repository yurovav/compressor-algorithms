import json
import sys

if len(sys.argv) != 3:
    print("Использование: python lz78_decompress.py archive.json restored.txt")
    raise SystemExit

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

dictionary = {}
next_index = 1
result = ""

for prefix_index, char in data:
    phrase = dictionary.get(prefix_index, "") + char
    result += phrase

    if char != "":
        dictionary[next_index] = phrase
        next_index += 1

with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write(result)

print("Разархивация завершена.")
print("Восстановлено символов:", len(result))
