
import argparse
import struct
import math

MAGIC = b"GMR1"
HEADER_FORMAT = "<4sQ256QQ"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def bits_to_bytes(bits):
    result = bytearray()
    for i in range(0, len(bits), 8):
        part = bits[i:i + 8]
        while len(part) < 8:
            part.append(0)

        value = 0
        for bit in part:
            value = (value << 1) | bit

        result.append(value)

    return bytes(result)


def bytes_to_bits(data, bit_count):
    bits = []

    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
            if len(bits) == bit_count:
                return bits

    return bits


def calculate_frequencies(data):
    frequencies = [0] * 256

    for byte in data:
        frequencies[byte] += 1

    return frequencies


def build_codes(frequencies):
    total = sum(frequencies)
    codes = {}
    cumulative = 0

    if total == 0:
        return codes

    for symbol in range(256):
        frequency = frequencies[symbol]

        if frequency == 0:
            continue

        length = 0
        while (1 << length) * frequency < total:
            length += 1

        length += 1

        numerator = 2 * cumulative + frequency
        denominator = 2 * total

        code_value = (numerator * (1 << length)) // denominator
        codes[symbol] = format(code_value, f"0{length}b")

        cumulative += frequency

    return codes


def gilbert_compress(data):
    frequencies = calculate_frequencies(data)
    codes = build_codes(frequencies)

    bits = []

    for byte in data:
        for bit in codes[byte]:
            bits.append(int(bit))

    return bits_to_bytes(bits), len(bits), frequencies


def gilbert_decompress(data, bit_count, original_size, frequencies):
    if original_size == 0:
        return b""

    codes = build_codes(frequencies)

    tree = {}

    for symbol, code in codes.items():
        node = tree

        for bit in code:
            if bit not in node:
                node[bit] = {}

            node = node[bit]

        node["symbol"] = symbol

    bits = bytes_to_bits(data, bit_count)
    result = bytearray()
    node = tree

    for bit in bits:
        if bit not in node:
            raise ValueError("Поврежденный архив.")

        node = node[bit]

        if "symbol" in node:
            result.append(node["symbol"])
            node = tree

            if len(result) > original_size:
                raise ValueError("Поврежденный архив.")

    if node is not tree or len(result) != original_size:
        raise ValueError("Не удалось восстановить файл.")

    return bytes(result)


def compress_file(input_filename, output_filename):
    with open(input_filename, "rb") as file:
        data = file.read()

    compressed_data, bit_count, frequencies = gilbert_compress(data)

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        len(data),
        *frequencies,
        bit_count
    )

    with open(output_filename, "wb") as file:
        file.write(header)
        file.write(compressed_data)

    print("Сжатие выполнено.")
    print("Исходный размер:", len(data), "байт")
    print("Размер архива:", HEADER_SIZE + len(compressed_data), "байт")


def decompress_file(input_filename, output_filename):
    with open(input_filename, "rb") as file:
        header = file.read(HEADER_SIZE)

        if len(header) != HEADER_SIZE:
            raise ValueError("Поврежденный архив.")

        unpacked = struct.unpack(HEADER_FORMAT, header)

        magic = unpacked[0]
        original_size = unpacked[1]
        frequencies = list(unpacked[2:258])
        bit_count = unpacked[258]

        if magic != MAGIC:
            raise ValueError("Это не архив Гилберта-Мура.")

        compressed_data = file.read()

    if sum(frequencies) != original_size:
        raise ValueError("Поврежденный архив.")

    if bit_count > len(compressed_data) * 8:
        raise ValueError("Поврежденный архив.")

    data = gilbert_decompress(
        compressed_data,
        bit_count,
        original_size,
        frequencies
    )

    with open(output_filename, "wb") as file:
        file.write(data)

    print("Восстановление выполнено.")
    print("Размер восстановленного файла:", len(data), "байт")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--decompress", action="store_true")
    parser.add_argument("input")
    parser.add_argument("output")

    args = parser.parse_args()

    if args.decompress:
        decompress_file(args.input, args.output)
    else:
        compress_file(args.input, args.output)


if __name__ == "__main__":
    main()
