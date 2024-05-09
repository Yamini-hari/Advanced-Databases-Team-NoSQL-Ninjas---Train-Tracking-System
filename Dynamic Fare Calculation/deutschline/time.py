import random
import string

def generate_random_string(length):
    alphanumeric_chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphanumeric_chars) for _ in range(length))

# Generate a 7-digit alphanumeric random string in uppercase
random_string = generate_random_string(7)
print("Random String (Uppercase):", random_string)
