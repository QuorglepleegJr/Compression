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

def EncodingError(Exception):

    pass

def DecodingError(Exception):

    pass

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
        raise EncodingError()
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
    body = bytearray(divide_into_bytes(value, data_length, padding=spare))

    with open(write_path, "wb") as out:

        out.write(header)
        out.write(body)

def read_file(inp):

    if inp[-4:] != ".huf":

        raise DecodingError

    read_path = os.path.join(os.getcwd(), inp)

    if not os.path.exists(read_path):

        raise DecodingError

    with open(read_path, "rb") as inp:

        value = int.from_bytes(inp.read(), "big")
        contents = 



#write_file("testing", get_compressed("THis IS a test Of Special characTerS!1!1"))
print(read_file("test.huf"))