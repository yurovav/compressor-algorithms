import argparse
import struct
import sys


MAGIC = b"BST1"
HEADER_FORMAT = "<4sQQ"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def bits_to_bytes(bits):
    """Преобразует строку битов в байты."""
    result = bytearray()

    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]

        if len(byte_bits) < 8:
            byte_bits += "0" * (8 - len(byte_bits))

        result.append(int(byte_bits, 2))

    return bytes(result)


def bytes_to_bits(data, bit_count):
    """Преобразует байты в строку заданного количества битов."""
    bits = ""

    for byte in data:
        bits += format(byte, "08b")

    if bit_count > len(bits):
        raise ValueError("Поврежденный файл: недостаточно данных")

    return bits[:bit_count]


def gamma_encode(number):
    """Кодирование положительного числа кодом Элиаса гамма."""
    if number <= 0:
        raise ValueError("Число должно быть положительным")

    binary = format(number, "b")
    return "0" * (len(binary) - 1) + binary


def gamma_decode(bits, position):
    """Декодирование одного числа из битовой строки."""
    zero_count = 0

    while position < len(bits) and bits[position] == "0":
        zero_count += 1
        position += 1

    if position >= len(bits):
        raise ValueError("Поврежденный файл: некорректный гамма-код")

    number_length = zero_count + 1

    if position + number_length > len(bits):
        raise ValueError("Поврежденный файл: неполный гамма-код")

    number = int(bits[position:position + number_length], 2)
    position += number_length

    return number, position


def bookstack_compress(data):
    """
    Сжатие алгоритмом «Стопка книг».

    Используется список из всех возможных байтов.
    После обработки символ перемещается в начало списка.
    """
    books = list(range(256))
    encoded_bits = []

    for symbol in data:
        index = books.index(symbol)

        # Индекс начинается с нуля, поэтому прибавляем 1.
        encoded_bits.append(gamma_encode(index + 1))

        # Перемещаем использованный байт в начало списка.
        books.pop(index)
        books.insert(0, symbol)

    bit_string = "".join(encoded_bits)

    return bits_to_bytes(bit_string), len(bit_string)


def bookstack_decompress(compressed_data, bit_count, original_size):
    """Восстановление исходных данных."""
    if original_size == 0:
        return b""

    bits = bytes_to_bits(compressed_data, bit_count)

    books = list(range(256))
    result = bytearray()
    position = 0

    for _ in range(original_size):
        number, position = gamma_decode(bits, position)
        index = number - 1

        if index < 0 or index >= 256:
            raise ValueError("Поврежденный файл: неверный индекс")

        symbol = books[index]
        result.append(symbol)

        # Выполняем такое же перемещение, как при сжатии.
        books.pop(index)
        books.insert(0, symbol)

    if position != bit_count:
        raise ValueError("Поврежденный файл: лишние данные")

    return bytes(result)


def compress_file(input_name, output_name):
    """Сжимает файл и записывает результат."""
    with open(input_name, "rb") as file:
        data = file.read()

    compressed_data, bit_count = bookstack_compress(data)

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        len(data),
        bit_count
    )

    with open(output_name, "wb") as file:
        file.write(header)
        file.write(compressed_data)

    print("Сжатие завершено.")
    print("Исходный размер:", len(data), "байт")
    print("Размер сжатого файла:", HEADER_SIZE + len(compressed_data), "байт")


def decompress_file(input_name, output_name):
    """Восстанавливает исходный файл."""
    with open(input_name, "rb") as file:
        header = file.read(HEADER_SIZE)

        if len(header) != HEADER_SIZE:
            raise ValueError("Некорректный заголовок файла")

        magic, original_size, bit_count = struct.unpack(
            HEADER_FORMAT,
            header
        )

        if magic != MAGIC:
            raise ValueError("Файл не является архивом Book Stack")

        compressed_data = file.read()

    expected_size = (bit_count + 7) // 8

    if len(compressed_data) != expected_size:
        raise ValueError("Поврежденный файл: неверный размер данных")

    data = bookstack_decompress(
        compressed_data,
        bit_count,
        original_size
    )

    with open(output_name, "wb") as file:
        file.write(data)

    print("Восстановление завершено.")
    print("Размер восстановленного файла:", len(data), "байт")


def main():
    parser = argparse.ArgumentParser(
        description="Архиватор на основе алгоритма «Стопка книг»"
    )

    parser.add_argument(
        "-d",
        "--decompress",
        action="store_true",
        help="Режим восстановления файла"
    )

    parser.add_argument("input", help="Входной файл")
    parser.add_argument("output", help="Выходной файл")

    args = parser.parse_args()

    try:
        if args.decompress:
            decompress_file(args.input, args.output)
        else:
            compress_file(args.input, args.output)

    except (OSError, ValueError, struct.error) as error:
        print("Ошибка:", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
