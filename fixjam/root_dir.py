import os

def root_dir(*args): 
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *args)

