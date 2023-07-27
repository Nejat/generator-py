# generator-py

With a desire to think through the many test scenarios of a `rust` project, and a recent requirement to pick up
`python` for my day job, I created this generic parametrically driven script for synthesizing unit tests that are
logically grouped.

Though I think it might be possible, in its current implementation the one included example does not generate complete
tests and requires further manual modification of the generated tests to have running tests.

## Test Data Structure

A test definition data structure is an array of module definitions.

A module definition is identified by either of the following fields;

* __module: _str___ identifies a parent namespace, in this case a rust crate
* __name: _str___ identifies a test file, which can contain nested modules

All modules, _namespaces_ or _test files_, can define the following fields;

* __modules: _list[dict]___ a collection of submodules, that provide a hierarchical definition of tests<br/><br/>
  _i.e._ Domain > Subject Under Test > Scenario Input > Action > Pass | Fail Tests<br/><br/>
* __mapped_modules: _dict___ a lookup of reusable module definitions<br/><br/>
* __applied_scenarios: _dict___ a lookup of scenarios that apply to current hierarchy of tests<br/><br/>
* __scenarios: _dict___ a collection of named scenario variant inputs and metadata<br/><br/>
* __test: _dict___ an object defining a test<br/><br/>
  _contains_: subject under test, input, action, actual, expected, optional post tests, test metadata, etc.

## Hierarchy of Test Definitions

All definitions within a module inherit from its parent module so that shared information does not need to be repeated
from module to module. Most fields of all objects defined in a parent module propagate to its children. Any field also
defined in a child will override the parent value. The exception to this is _given_ and _args_ fields of test
definitions, they are concatenated.

Additionally, `applied_scenarios`, `module_mappings` and `scenarios` can add to parent values rather than override time
with their plus variants; `applied_scenarios_plus`, `module_mappings_plus` and `scenarios_plus`

_* in its current state, the one example script does correctly generate the expected tests, however the concept of
the `plus` variants are coded but not completely tested yet._

## Code Templates and Test Arguments

Test definitions support code templates to further reduce definition duplication, basically providing a mechanism for
testing different input values with tests. Test definitions have a `args` lookup field and `applied_scenarios` determine
what `scenario` variants apply to test modules as well as additional arguments. Test code should use Python's named text
templating mechanism to define test code to accept arguments, _i.e._ `'foo = %(foo_value)s`. Arguments are applied
recursively, so arguments can contain more templates themselves.

## Example Test Definition

```json
[
  {
    "module": "TestDomain",
    "modules": [
      {
        "module": "TestSubject",
        "modules": [
          {
            "module": "TestScenarioInput",
            "applied_scenarios": {
              "action": {
                "err": {
                  "scenario variant 1": {},
                  "scenario variant 3": {},
                  "scenario variant n1": {}
                },
                "ok": {
                  "scenario variant 2": {
                    "test arg a": "arg a value",
                    "test arg b": "arg v value"
                  },
                  "scenario variant 5": {
                    "test arg a": "arg a value",
                    "test arg b": "arg v value"
                  },
                  "scenario variant n2": {
                    "test arg a": "arg a value",
                    "test arg b": "arg v value"
                  }
                }
              }
            },
            "modules": [
              "action"
            ],
            "test": {
              "args": {
                "test arg 1": "value"
              },
              "given": "required; describe scenario",
              "sut": "required; subject under test for scenario"
            }
          }
        ]
      }
    ],
    "mapped_modules": {
      "action": {
        "name": "action",
        "modules": [
          "err",
          "ok"
        ],
        "test": {
          "action": "optional; action (defaults to module name)",
          "actual": "required; actual code"
        }
      },
      "err": {
        "name": "err",
        "test": {
          "expected": "required; some err code",
          "post_test": "optional; some post test code",
          "success": "optional; true(default) | false; flag indicates expected fail or success"
        }
      }
    },
    "scenarios": {
      "formatting": {
        "err": "formatting or value for err conditions",
        "ok": "formatting or value for ok conditions"
      },
      "ordered_labels": [
        {
          "doc_label": "used for labeling test matrix markdown doc",
          "variant": "name of variant"
        }
      ],
      "suffix": "test name suffix",
      "variants": {
        "some test variant (descriptive)": {
          "some test input": "test input code"
        }
      }
    },
    "test": {
      "args": {
        "arg 1": "arg 1 value",
        "arg 2": "arg 2 value",
        "arg n": "arg n value"
      }
    }
  }
]
```

<br/>

For a complete test definition see the [`kabufuda.json`](kabufuda.json) example in the project.

## Command Line Arguments

* test definition json path
* `-c`, `--clean` re-formats and sorts test definition json
* `-d`, `--debug`_optional_, outputs debug information
* `-r`, `--root` _optional_, root output path of tests, defaults to current path

### How to Run Script

```shell
py generate.py kabufuda.json -r project/src/tests/game -d
```

### Example Output

```
Test Generator: 'kabufuda.json'
Test Root Path: 'project/src/tests/game'

\pieces
  \column
    mod card;
      mod put {
        mod err {
        }
        mod ok {
        }
      }
      mod take {
        mod err {
        }
        mod ok {
        }
      }
    mod partial;
      mod put {
        mod err {
        }
        mod ok {
        }
      }
      mod take {
        mod err {
        }
        mod ok {
        }
      }
    mod multi_partial;
      mod put {
        mod err {
        }
        mod ok {
        }
      }
      mod take {
        mod err {
        }
        mod ok {
        }
      }
    mod full_set;
      mod put {
        mod err {
        }
      }
      mod take {
        mod err {
        }
        mod ok {
        }
      }
    mod complete;
      mod put {
        mod err {
        }
      }
      mod take {
        mod err {
        }
      }
    mod empty;
      mod put {
        mod err {
        }
        mod ok {
        }
      }
      mod take {
        mod err {
        }
      }
  \slot
    mod card;
      mod put {
        mod err {
        }
        mod ok {
        }
      }
      mod take {
        mod err {
        }
        mod ok {
        }
      }
    mod complete;
      mod put {
        mod err {
        }
      }
      mod take {
        mod err {
        }
      }
    mod empty;
      mod put {
        mod err {
        }
        mod ok {
        }
      }
      mod take {
        mod err {
        }
      }
    mod locked;
      mod put {
        mod err {
        }
      }
      mod take {
        mod err {
        }
      }

Formatting Rust test files in project\src\tests\game ...

project\src\tests\game\mod.rs
project\src\tests\game\pieces\mod.rs
project\src\tests\game\pieces\column\card.rs
project\src\tests\game\pieces\column\complete.rs
project\src\tests\game\pieces\column\empty.rs
project\src\tests\game\pieces\column\full_set.rs
project\src\tests\game\pieces\column\mod.rs
project\src\tests\game\pieces\column\multi_partial.rs
project\src\tests\game\pieces\column\partial.rs
project\src\tests\game\pieces\slot\card.rs
project\src\tests\game\pieces\slot\complete.rs
project\src\tests\game\pieces\slot\empty.rs
project\src\tests\game\pieces\slot\locked.rs
project\src\tests\game\pieces\slot\mod.rs
```