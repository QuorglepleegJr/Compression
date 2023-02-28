import os

'''

FILE FORMAT:

Header:

4 Bytes: "HUFF", signature
2 Bytes: Header length (includes dictionary), most significant first
1 Bytes: Number of entries in dictionary, most significant first
4 Bytes: Data length in bytes, most significant first
1 Byte: Number of spare bits left in last byte

Dictionary:
 
1 Byte: Char code in ascii
1 Byte: Length in bits of code
2 Bytes: Code

Data:

Just a massive string of binary, finishing with 0 bits to pad out last byte

'''

class EncodingError(Exception):

    pass

class DecodingError(Exception):

    pass

def convert_to_int(values):

    total = 0

    for x in range(len(values), 0, -1):

        total += values[-x] * 256**(x-1)

    return total

def divide_into_bytes(value, length=None, padding=0):

    if length is None:

        length = (value.bit_length() + 7) // 8

    value *= 2**padding

    out = [0 for x in range(length)]

    for x in range(length, 0, -1):

        out[length-x] = value // 256**(x-1)

        value %= 256**(x-1)

    return out

def byte_codes(string):

    counts = {}
    codes = {}

    for char in string:

        try:

            counts[char] += 1

        except KeyError:

            counts[char] = 1

    while len(counts) > 1:

        small = ""
        smallest = ""

        for key in counts:

            try:

                if counts[key] < counts[smallest]:
                    
                    try:

                        if counts[smallest] < counts[small]:

                            small = smallest
                
                    except KeyError:

                        small = smallest

                    smallest = key

            except KeyError:

                smallest = key

            try:

                if  smallest != key and counts[key] < counts[small]:

                    small = key

            except KeyError:

                small = key

        counts[smallest + small] = counts[smallest] + counts[small]
        counts.pop(smallest)
        counts.pop(small)

        if len(counts) != 1:

            codes[smallest] = (smallest+small, "0")
            codes[small] = (smallest+small, "1")

        else:

            codes[smallest] = (None, "0")
            codes[small] = (None, "1")

    return codes

def get_bytecode(key, codes):

    if codes[key][0] == None:  return codes[key][1]

    return get_bytecode(codes[key][0], codes) + codes[key][1]


def get_codes(string):

    codes = byte_codes(string)

    char_codes = {}

    for key in codes:

        if len(key) == 1:

            char_codes[key] = get_bytecode(key, codes)

            print(f"Code for '{key}' is {get_bytecode(key, codes)}")

    print(char_codes)

    return char_codes

def get_compressed(string):
    
    char_codes = get_codes(string)

    compressed = ""

    for char in string:

        compressed += char_codes[char]
    
    print(compressed)
    print(len(compressed))
    
    return compressed, char_codes

def retrieve_original(encoded, char_codes):

    reverse_dict = {}

    for key in char_codes:

        reverse_dict[char_codes[key]] = key

    current_decode = ""
    decoded = ""

    while len(encoded) > 0:

        digit = encoded[0]

        current_decode += digit
        
        if current_decode in reverse_dict:

            decoded += reverse_dict[current_decode]
            current_decode = ""

        encoded = encoded[1:]

    print("DECODED:", decoded)

    return decoded

def write_file(name, compressed):

    write_path = os.path.join(os.getcwd(), f"{name}.huf")

    count = 0

    while os.path.exists(write_path):

        count += 1
        
        write_path = os.path.join(os.getcwd(), f"{name}({count}).huf")

    header = bytearray()

    header += b'HUFF'

    header += bytes(divide_into_bytes(12+4*len(compressed[1]),2))

    l = len(compressed[1])
    if l >= 256:
        raise EncodingError("Tree too long, must be fewer than 256 elements")
    header += bytes([l])

    l = len(compressed[0])

    data_length = (l+7)//8
    header += bytes(divide_into_bytes(data_length, 4))

    spare = 8-l%8
    header += bytes([spare])
    
    dict_bytes = bytearray()

    for char in compressed[1]:

        if ord(char) >= 256:

            raise EncodingError
        
        dict_bytes += bytes([ord(char), len(compressed[1][char]), \
            *divide_into_bytes(int(compressed[1][char], 2), 2)])
    
    header += dict_bytes

    value = int(compressed[0], 2)
    print("HERE'S WHERE TO STOP")
    body = bytearray(divide_into_bytes(value, data_length, padding=spare))

    with open(write_path, "wb") as out:

        out.write(header)
        out.write(body)

    return f"Written to {write_path.rsplit('/')[0]}"

def convert_file(inp):

    types = {".huf": from_huf,
             ".txt": from_txt}

    for extension in types:
        
        if inp.endswith(extension) and \
            os.path.isfile(os.path.join(os.getcwd(), inp)):

            return types[extension](os.path.join(os.getcwd(), inp))

    raise DecodingError("Invalid file type to convert")

def from_txt(read_path, name=None):

    with open(read_path) as inp:

        text = inp.read().rstrip()
    
    compressed = get_compressed(text)
    
    if name is None:

        name = read_path.rsplit("/")[0]

    return write_file(name, compressed)

def from_huf(read_path):

    text = read_huf(read_path)

    write_path = read_path[:-4] + ".txt"

    count = 0

    while os.path.isfile(write_path):

        write_path = read_path[:-4] + f"({count}).txt"
        count += 1

    with open(read_path[:-3]+"txt", "w") as out:

        out.write(text)
    
    return text

def read_huf(read_path):

    with open(read_path, "rb") as inp:

        value = int.from_bytes(inp.read(), "big")
        
    size = (value.bit_length() + 7) // 8

    content = divide_into_bytes(value, size)

    if content[:4] != [72, 85, 70, 70]:

        raise DecodingError("Supplied .huf had incorrect signature")

    header_length = convert_to_int(content[4:6])

    info = content[6:12]
    dictionary = content[12:header_length]
    body = content[header_length:]

    print(info, dictionary, body)

    chars = {}
    for index in range(len(dictionary)//4):

        char = dictionary[index*4:index*4+4]

        code = bin(convert_to_int(char[2:]))[2:]

        while len(code) < char[1]:

            code = "0" + code

        chars[chr(char[0])] = code

    spare = info[5]

    encoded = bin(convert_to_int(body))[2:]

    while len(encoded) % 8 != 0:

        encoded = "0" + encoded

    encoded = encoded[:-spare]

    print(chars, "\n",encoded)

    return retrieve_original(encoded, chars)