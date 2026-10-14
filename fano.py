import argparse
import struct
import heapq

MAGIC = b"CMP1"
HEADER_FORMAT = "<4sBQ256Q"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def bits_to_bytes(bits):

    result = bytearray()
    current_byte = 0
    bit_count = 0

    for bit in bits:
        current_byte = (current_byte << 1) | bit
        bit_count += 1

        if bit_count == 8:
            result.append(current_byte)
            current_byte = 0
            bit_count = 0

    if bit_count != 0:
        current_byte <<= (8 - bit_count)
        result.append(current_byte)

    return bytes(result)


def bytes_to_bits(data, bit_count):
    bits = []

    for byte in data:
        for i in range(7, -1, -1):
            if len(bits) == bit_count:
                return bits

            bits.append((byte >> i) & 1)

    return bits


def build_fano_codes(frequencies):
    symbols = [
        (symbol, frequencies[symbol])
        for symbol in range(256)
        if frequencies[symbol] > 0
    ]

    if not symbols:
        return {}
    symbols.sort(key=lambda x: (-x[1], x[0]))

    codes = {symbol: "" for symbol, _ in symbols}

    # Один уникальный символ.
    if len(symbols) == 1:
        codes[symbols[0][0]] = "0"
        return codes

    def split(items):
        if len(items) <= 1:
            return

        total = sum(freq for _, freq in items)

        best_index = 1
        best_difference = float("inf")
        left_sum = 0

        for i in range(1, len(items)):
            left_sum += items[i - 1][1]
            right_sum = total - left_sum

            difference = abs(left_sum - right_sum)

            if difference < best_difference:
                best_difference = difference
                best_index = i

        left = items[:best_index]
        right = items[best_index:]

        for symbol, _ in left:
            codes[symbol] += "0"

        for symbol, _ in right:
            codes[symbol] += "1"

        split(left)
        split(right)

    split(symbols)

    return codes


def fano_compress(data, frequencies):

    codes = build_fano_codes(frequencies)

    bits = []

    for byte in data:
        code = codes[byte]

        for bit in code:
            bits.append(int(bit))

    return bits_to_bytes(bits), len(bits)


def fano_decompress(data, frequencies, bit_count):
    codes = build_fano_codes(frequencies)

    if not codes:
        return b""


    if len(codes) == 1:
        symbol = next(iter(codes))
        total_size = sum(frequencies)
        return bytes([symbol]) * total_size

    reverse_codes = {
        code: symbol
        for symbol, code in codes.items()
    }

    bits = bytes_to_bits(data, bit_count)

    result = bytearray()
    current_code = ""

    for bit in bits:
        current_code += str(bit)

        if current_code in reverse_codes:
            result.append(reverse_codes[current_code])
            current_code = ""

    return bytes(result)


def calculate_frequencies(data):

    frequencies = [0] * 256

    for byte in data:
        frequencies[byte] += 1

    return frequencies


def write_compressed_file(filename, algorithm, original_size,
                          frequencies, bit_count, compressed_data):
    """Записывает сжатый файл."""

    algorithm_id = {
        "haffman": 1,
        "fano": 2,
        "shannon": 3
    }[algorithm]

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        algorithm_id,
        original_size,
        *frequencies
    )

    bit_header = struct.pack("<Q", bit_count)

    with open(filename, "wb") as file:
        file.write(header)
        file.write(bit_header)
        file.write(compressed_data)


def read_compressed_file(filename):

    with open(filename, "rb") as file:
        header = file.read(HEADER_SIZE)

        if len(header) != HEADER_SIZE:
            raise ValueError("Файл слишком короткий или поврежден.")

        unpacked = struct.unpack(HEADER_FORMAT, header)

        magic = unpacked[0]
        algorithm_id = unpacked[1]
        original_size = unpacked[2]
        frequencies = list(unpacked[3:])

        if magic != MAGIC:
            raise ValueError("Это не файл данного архиватора.")

        bit_header = file.read(8)

        if len(bit_header) != 8:
            raise ValueError("Поврежден заголовок файла.")

        bit_count = struct.unpack("<Q", bit_header)[0]

        compressed_data = file.read()

    algorithms = {
        1: "haffman",
        2: "fano",
        3: "shannon"
    }

    if algorithm_id not in algorithms:
        raise ValueError("Неизвестный алгоритм.")

    return (
        algorithms[algorithm_id],
        original_size,
        frequencies,
        bit_count,
        compressed_data
    )


def compress_file(input_filename, output_filename):
    with open(input_filename, "rb") as file:
        data = file.read()

    frequencies = calculate_frequencies(data)
    compressed_data, bit_count = fano_compress(data, frequencies)
    write_compressed_file(
        output_filename, "fano", len(data), frequencies,
        bit_count, compressed_data
    )

    print("Сжатие выполнено.")
    print(f"Исходный размер: {len(data)} байт")
    print(f"Размер сжатого файла: {HEADER_SIZE + 8 + len(compressed_data)} байт")
    print("Алгоритм: fano")


def decompress_file(input_filename, output_filename):
    algorithm, original_size, frequencies, bit_count, compressed_data = read_compressed_file(input_filename)
    if algorithm != "fano":
        raise ValueError("Архив создан другим алгоритмом: " + algorithm)

    data = fano_decompress(compressed_data, frequencies, bit_count)
    if len(data) != original_size:
        raise ValueError("Размер восстановленного файла не совпадает с исходным.")

    with open(output_filename, "wb") as file:
        file.write(data)

    print("Восстановление выполнено.")
    print(f"Размер восстановленного файла: {len(data)} байт")
    print("Алгоритм: fano")


def main():
    parser = argparse.ArgumentParser(description="Архиватор с алгоритмом fano.")
    parser.add_argument("-d", "--decompress", action="store_true", help="Распаковать файл")
    parser.add_argument("input", help="Входной файл")
    parser.add_argument("output", help="Выходной файл")
    args = parser.parse_args()
    if args.decompress:
        decompress_file(args.input, args.output)
    else:
        compress_file(args.input, args.output)


if __name__ == "__main__":
    main()
