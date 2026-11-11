import argparse
import struct


MAGIC = b"AHF1"
HEADER_FORMAT = "<4sQ"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class Node:
    def __init__(self, weight, order, symbol=None, parent=None):
        self.weight = weight
        self.order = order
        self.symbol = symbol
        self.parent = parent
        self.left = None
        self.right = None

    def is_leaf(self):
        return self.left is None and self.right is None


class AdaptiveHuffman:
    def __init__(self):
        self.root = Node(0, 511)
        self.nyt = self.root
        self.symbol_nodes = {}
        self.nodes = [self.root]

    def _get_path(self, node):
        bits = []
        while node.parent is not None:
            bits.append(0 if node.parent.left is node else 1)
            node = node.parent
        return bits[::-1]

    def _is_ancestor(self, ancestor, node):
        current = node.parent
        while current is not None:
            if current is ancestor:
                return True
            current = current.parent
        return False

    def _swap_nodes(self, first, second):
        parent_first = first.parent
        parent_second = second.parent

        if parent_first is None or parent_second is None:
            return

        if parent_first is parent_second:
            if parent_first.left is first:
                parent_first.left, parent_first.right = second, first
            else:
                parent_first.left, parent_first.right = first, second
        else:
            if parent_first.left is first:
                parent_first.left = second
            else:
                parent_first.right = second

            if parent_second.left is second:
                parent_second.left = first
            else:
                parent_second.right = first

            first.parent = parent_second
            second.parent = parent_first

        first.order, second.order = second.order, first.order

    def _update_tree(self, node):
        while node is not None:
            leader = node

            for candidate in self.nodes:
                if (
                    candidate.weight == node.weight
                    and candidate.order > leader.order
                    and candidate is not node
                    and not self._is_ancestor(candidate, node)
                    and not self._is_ancestor(node, candidate)
                ):
                    leader = candidate

            if leader is not node:
                self._swap_nodes(node, leader)

            node.weight += 1
            node = node.parent

    def _add_new_symbol(self, symbol):
        old_nyt = self.nyt
        new_nyt = Node(0, old_nyt.order - 2, parent=old_nyt)
        new_leaf = Node(0, old_nyt.order - 1, symbol=symbol,
                        parent=old_nyt)

        old_nyt.left = new_nyt
        old_nyt.right = new_leaf
        self.nyt = new_nyt
        self.symbol_nodes[symbol] = new_leaf
        self.nodes.extend([new_nyt, new_leaf])
        self._update_tree(old_nyt)

    def encode_symbol(self, symbol, output_bits):
        if symbol in self.symbol_nodes:
            node = self.symbol_nodes[symbol]
            output_bits.extend(self._get_path(node))
            self._update_tree(node)
        else:
            output_bits.extend(self._get_path(self.nyt))
            output_bits.extend((symbol >> shift) & 1
                               for shift in range(7, -1, -1))
            self._add_new_symbol(symbol)

    def decode_symbol(self, read_bit):
        node = self.root
        while not node.is_leaf():
            bit = read_bit()
            node = node.right if bit else node.left

        if node is self.nyt:
            symbol = 0
            for _ in range(8):
                symbol = (symbol << 1) | read_bit()
            self._add_new_symbol(symbol)
            return symbol

        symbol = node.symbol
        self._update_tree(node)
        return symbol


def bits_to_bytes(bits):
    result = bytearray()
    current = 0
    count = 0

    for bit in bits:
        current = (current << 1) | bit
        count += 1
        if count == 8:
            result.append(current)
            current = 0
            count = 0

    if count:
        result.append(current << (8 - count))

    return bytes(result)


def bytes_to_bits(data, bit_count):
    bits = []
    for byte in data:
        for shift in range(7, -1, -1):
            if len(bits) >= bit_count:
                return bits
            bits.append((byte >> shift) & 1)
    return bits


def adaptive_compress(data):
    coder = AdaptiveHuffman()
    bits = []
    for symbol in data:
        coder.encode_symbol(symbol, bits)
    return bits_to_bytes(bits), len(bits)


def adaptive_decompress(data, bit_count, original_size):
    if original_size == 0:
        return b""

    bits = bytes_to_bits(data, bit_count)
    position = 0

    def read_bit():
        nonlocal position
        if position >= len(bits):
            raise ValueError("Поврежденный архив: неожиданный конец данных.")
        bit = bits[position]
        position += 1
        return bit

    coder = AdaptiveHuffman()
    result = bytearray()

    for _ in range(original_size):
        result.append(coder.decode_symbol(read_bit))

    if position != bit_count:
        raise ValueError("Поврежденный архив: лишние биты после распаковки.")

    return bytes(result)


def compress_file(input_filename, output_filename):
    with open(input_filename, "rb") as file:
        original = file.read()

    compressed, bit_count = adaptive_compress(original)
    header = struct.pack(HEADER_FORMAT, MAGIC, len(original))
    bit_header = struct.pack("<Q", bit_count)

    with open(output_filename, "wb") as file:
        file.write(header)
        file.write(bit_header)
        file.write(compressed)

    print("Сжатие выполнено.")
    print(f"Исходный размер: {len(original)} байт")
    print(f"Размер архива: {HEADER_SIZE + 8 + len(compressed)} байт")


def decompress_file(input_filename, output_filename):
    with open(input_filename, "rb") as file:
        header = file.read(HEADER_SIZE)
        if len(header) != HEADER_SIZE:
            raise ValueError("Файл слишком короткий или поврежден.")

        magic, original_size = struct.unpack(HEADER_FORMAT, header)
        if magic != MAGIC:
            raise ValueError("Это не архив Adaptive Huffman.")

        bit_header = file.read(8)
        if len(bit_header) != 8:
            raise ValueError("Поврежден заголовок архива.")

        bit_count = struct.unpack("<Q", bit_header)[0]
        compressed = file.read()

    restored = adaptive_decompress(
        compressed, bit_count, original_size
    )

    with open(output_filename, "wb") as file:
        file.write(restored)

    print("Восстановление выполнено.")
    print(f"Размер восстановленного файла: {len(restored)} байт")


def main():
    parser = argparse.ArgumentParser(
        description="Архиватор с адаптивным кодом Хаффмана."
    )
    parser.add_argument(
        "-d", "--decompress", action="store_true",
        help="Распаковать архив"
    )
    parser.add_argument("input", help="Входной файл")
    parser.add_argument("output", help="Выходной файл")
    args = parser.parse_args()

    if args.decompress:
        decompress_file(args.input, args.output)
    else:
        compress_file(args.input, args.output)


if __name__ == "__main__":
    main()
