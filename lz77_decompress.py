import json
import sys

if len(sys.argv) != 3:
    print("Использование: python lz77_decompress.py archive.json restored.txt")
    raise SystemExit

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

result = ""

for distance, length, next_char in data:
    if distance > 0:
        for _ in range(length):
            result += result[-distance]

    result += next_char

with open(sys.argv[2], "w", encoding="utf-8") as f:
    f.write(result)

print("Разархивация завершена.")
print("Восстановлено символов:", len(result))
