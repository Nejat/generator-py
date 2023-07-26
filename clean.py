import os
import subprocess

import logic


# format all *.rs files recursively under a root path
def format_rust_files(root: str) -> None:
    # normalize os path separators of the root path
    root = root.replace('\\', '/').replace('/', os.path.sep)

    # format the rust file in a path
    def fmt_code(path: str, file: str) -> None:
        # create and normalize os path separators of a code path
        code_path = os.path.join(path, file).replace('\\', '/').replace('/', os.path.sep)

        # debug output of code file being formatted
        if logic.output_debugging:
            print(code_path)

        # run rustfmt command as subprocess
        subprocess.run(['rustfmt', code_path])

    # debug output of formatting of generated rust files
    if logic.output_debugging:
        print('Formatting Rust test files in %s ...' % root)
        print()

    # walk root path and format only *.rs code files
    [fmt_code(path, file) for (path, _, files) in os.walk(root) for file in files if file.endswith(".rs")]
