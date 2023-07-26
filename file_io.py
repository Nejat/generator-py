import os
from typing import Callable


# append data from a lambda function to a file
def append_to_file(file_name: str, data: Callable) -> None:
    with open(file_name, 'a') as output:
        output.write(data())
        output.write('\n')


# determine if a file contains some content on any given line
def file_contains(file_path: str, content: str) -> bool:
    # does not contain content if file does not exist
    if not os.path.exists(file_path):
        return False

    # open file and check every line for content
    with open(file_path, 'r') as checked_file:
        contained = any([True for line in checked_file.readlines() if content in line])

    # return result
    return contained


# sets the current working directory to the parent folder
def go_back_a_folder() -> None:
    os.chdir(os.path.pardir)


# sets the current working directory to a path in the current folder
def goto_folder(path: str) -> None:
    # build folder path
    module_path = os.path.join(os.path.curdir, path)

    # create folder if it does not exist
    if not os.path.exists(module_path):
        os.makedirs(module_path)

    # check if path is a folder
    if os.path.isdir(module_path):
        # if so, make it the current folder
        os.chdir(module_path)
    else:
        # otherwise it's an exception
        raise Exception("'%s' is not a folder" % module_path)
