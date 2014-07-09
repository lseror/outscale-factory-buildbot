#!/usr/bin/env python
"""
Tool used to generate a password.
"""
import random
import string

random.seed()


def generate_password(minlen=32, maxlen=64):
    """
    Generate a random password for slave instances.
    """
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for i in range(random.randint(minlen, maxlen)))


def main():
    """
    Main function.
    """
    print generate_password()


if __name__ == '__main__':
    main()
