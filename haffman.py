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


def huffman_compress(data, frequencies):
    root = build_huffman_tree(frequencies)
    codes = build_huffman_codes(root)

    bits = []

    for byte in data:
        code = codes[byte]

        for bit in code:
            bits.append(int(bit))

    return bits_to_bytes(bits), len(bits)


def huffman_decompress(data, frequencies, bit_count):
    root = build_huffman_tree(frequencies)

    if root is None:
        return b""

    # Особый случай: файл состоит из одного повторяющегося байта.
    if root.symbol is not None:
        total_size = sum(frequencies)
        return bytes([root.symbol]) * total_size

    bits = bytes_to_bits(data, bit_count)

    result = bytearray()
    current = root

    for bit in bits:
        if bit == 0:
            current = current.left
        else:
            current = current.right

        if current.symbol is not None:
            result.append(current.symbol)
            current = root

    return bytes(result)


def build_huffman_tree(frequencies):

    heap = []
    counter = 0

    for symbol in range(256):
        if frequencies[symbol] > 0:
            node = HuffmanNode(frequencies[symbol], symbol)
            heapq.heappush(heap, (frequencies[symbol], counter, node))
            counter += 1

    if not heap:
        return None

    if len(heap) == 1:
        return heap[0][2]

    while len(heap) > 1:
        freq1, _, left = heapq.heappop(heap)
        freq2, _, right = heapq.heappop(heap)

        parent = HuffmanNode(
            freq1 + freq2,
            left=left,
            right=right
        )

        heapq.heappush(heap, (parent.frequency, counter, parent))
        counter += 1

    return heap[0][2]


def build_huffman_codes(root):

    codes = {}

    if root is None:
        return codes

    if root.symbol is not None:
        codes[root.symbol] = "0"
        return codes

    def walk(node, code):
        if node.symbol is not None:
            codes[node.symbol] = code
            return

        walk(node.left, code + "0")
        walk(node.right, code + "1")

    walk(root, "")
    return codes


class HuffmanNode:
    def __init__(self, frequency, symbol=None, left=None, right=None):
        self.frequency = frequency
        self.symbol = symbol
        self.left = left
        self.right = right


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
    compressed_data, bit_count = huffman_compress(data, frequencies)
    write_compressed_file(
        output_filename, "haffman", len(data), frequencies,
        bit_count, compressed_data
    )

    print("Сжатие выполнено.")
    print(f"Исходный размер: {len(data)} байт")
    print(f"Размер сжатого файла: {HEADER_SIZE + 8 + len(compressed_data)} байт")
    print("Алгоритм: haffman")


def decompress_file(input_filename, output_filename):
    algorithm, original_size, frequencies, bit_count, compressed_data = read_compressed_file(input_filename)
    if algorithm != "haffman":
        raise ValueError("Архив создан другим алгоритмом: " + algorithm)

    data = huffman_decompress(compressed_data, frequencies, bit_count)
    if len(data) != original_size:
        raise ValueError("Размер восстановленного файла не совпадает с исходным.")

    with open(output_filename, "wb") as file:
        file.write(data)

    print("Восстановление выполнено.")
    print(f"Размер восстановленного файла: {len(data)} байт")
    print("Алгоритм: haffman")


def main():
    parser = argparse.ArgumentParser(description="Архиватор с алгоритмом haffman.")
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
