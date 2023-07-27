import argparse
import json
import os

import logic
from clean import format_rust_files
from file_io import goto_folder
from logic import generate_tests, get_module_name


def generate_unit_tests(modules: list[{}], root: str) -> None:
    # capture current working directory
    cwd = os.path.realpath(os.path.curdir)

    # start generating in root folder
    goto_folder(root)

    # generate tests
    for module in modules:
        generate_tests(module)

    # return to starting working directory
    os.chdir(cwd)


if __name__ == '__main__':
    # define argument parser
    parser = argparse.ArgumentParser(
        prog='TestGenerator',
        description='Generate Rust Unit Testing Template',
    )

    # define required and optional arguments
    parser.add_argument('definitions')
    parser.add_argument('-r', '--root', default='tests')
    parser.add_argument('-c', '--clean', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')

    # parse arguments
    args = parser.parse_args()

    # set output debugging flag
    logic.output_debugging = args.debug

    print("Test Generator: '%s'" % args.definitions)
    print("Test Root Path: '%s'" % args.root)
    print()

    # read test definitions file
    with open(args.definitions, 'r') as json_file:
        definitions = json.load(json_file)

    if args.clean:
        # clean/re-format definitions json
        print('Clean Test Definitions')

        definitions.sort(key=lambda module: get_module_name(module))

        with open(args.definitions, 'w') as json_file:
            json.dump(definitions, json_file, indent=4, sort_keys=True)
    else:
        # generate tests from test definitions in the root folder
        generate_unit_tests(definitions, root=args.root)

        if logic.output_debugging:
            print()

        # format generated tests
        format_rust_files(args.root)
