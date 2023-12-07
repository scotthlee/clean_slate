import platform
import os
import openai


def get_base_dir():
    """Fetches a user directory based on the operating system."""
    OS = platform.system()
    if OS == 'Darwin':
        base_dir = '/Users/scottlee/'
    elif OS == 'Windows':
        base_dir = 'C:/Users/yle4/'
    elif OS == 'Linux':
        base_dir = '/mnt/c/Users/yle4/'
    return base_dir
