import os
from enum import Enum

from file_io import append_to_file, file_contains, goto_folder, go_back_a_folder

# labels of fields in definitions object
ACTION: str = 'action'
APPLIED_SCENARIOS: str = 'applied_scenarios'
APPLIED_SCENARIOS_PLUS: str = 'applied_scenarios+'
FORMATTING: str = 'formatting'
LABEL: str = 'doc_label'
MAPPINGS: str = 'module_mappings'
MAPPINGS_PLUS: str = 'module_mappings+'
MODULE: str = 'module'
MODULES: str = 'modules'
NAME: str = 'name'
ORDERED_LABELS: str = 'ordered_labels'
SCENARIOS: str = 'scenarios'
SCENARIOS_PLUS: str = 'scenarios+'
SUFFIX: str = 'suffix'
TEST: str = 'test'
TEST_ACTION: str = 'action'
TEST_ACTUAL: str = 'actual'
TEST_CODE: str = 'code'
TEST_ARGS: str = 'args'
TEST_EXPECTED: str = 'expected'
TEST_GIVEN: str = 'given'
TEST_POST: str = 'post_test'
TEST_POST_CODE: str = 'post_code'
TEST_SHOULD: str = 'should'
TEST_SUT: str = 'sut'
VARIANT: str = 'variant'
VARIANTS: str = 'variants'

# file name constants
MOD_RS: str = 'mod.rs'
TESTS_DOC = 'tests.md'


# the stages of modules
class Stage(Enum):
    FILE = 1
    FOLDER = 2
    IN_FILE = 3


# flag for enabling/disabling debugging output
output_debugging = False


# TODO: haven't tested additional module mappings, scenarios or applied scenarios

def generate_tests(
        module: {},
        parent_test: {} = None,
        module_mappings: {} = None,
        scenarios: {} = None,
        applied: dict | list = None,
        level: int = 0,
        test_file: str = None,
        file_level: int = 0
) -> None:
    _validate_module(module)

    # get name of current module
    module_name = get_module_name(module)

    # get test of current module
    module_test = _get_module_test(module, parent_test or {})

    # get module mappings of current module, otherwise use module mappings from parent
    module_mappings = _get_module_mappings(module, module_mappings)

    # use scenarios of current module, otherwise use scenarios from parent; test scenarios
    scenarios = _get_module_scenarios(module, scenarios)

    # get applied scenarios of current module
    applied = _get_module_applied_scenarios(module_name, module, applied)

    # get submodules of current module
    submodules = _get_module_submodules(module, module_mappings)

    # determine stage of current module
    stage = _get_module_stage(module, submodules)

    # module should have an action defined if not in file
    action = module[ACTION] if ACTION in module else module_name

    match stage:
        # process file module tests
        case Stage.FILE:
            if output_debugging:
                print('%smod %s;' % ('  ' * level, module_name))

            # create/overwrite module file
            module_file = '%s.rs' % module_name

            # create/overwrite module file
            open(module_file, 'w')

            # register module file in current module folder
            _register_rs_module(module_name, os.path.curdir)
            _generate_test_scenarios(module_test, scenarios, applied, action, module_file)

            _generate_tests_for_submodules(
                submodules, module_test, scenarios, applied,
                module_mappings, level, module_file, 0
            )

        # process folder module tests
        case Stage.FOLDER:
            if output_debugging:
                print('%s\\%s' % ('  ' * level, module_name))

            goto_folder(module_name)

            # register module folder with parent module
            _register_rs_module(module_name, os.path.pardir)
            _generate_test_scenarios(module_test, scenarios, applied, action, MOD_RS)

            # don't create a test doc if submodules are not all files
            if all([stage == Stage.FILE for stage in _submodule_stages(submodules, module_mappings)]):
                _create_test_doc(module_name, submodules, scenarios, applied, module_mappings)

            _generate_tests_for_submodules(
                submodules, module_test, scenarios, applied, module_mappings, level
            )

            go_back_a_folder()

        # process tests for embedding modules in current file module
        case Stage.IN_FILE:
            if output_debugging:
                print('%smod %s {' % ('  ' * level, module_name))

            if test_file is None or file_level is None:
                raise Exception('Expecting a test file and file level')

            append_to_file(test_file, lambda: '%smod %s {' % ('  ' * file_level, module_name))
            _generate_test_scenarios(module_test, scenarios, applied, action, test_file)

            _generate_tests_for_submodules(
                submodules, module_test, scenarios, applied,
                module_mappings, level, test_file, file_level + 1
            )

            append_to_file(test_file, lambda: '%s}' % ('  ' * file_level))

            if output_debugging:
                print('%s}' % ('  ' * level))


# gets the module name, either from name or module fields
def get_module_name(module):
    return module[NAME] if NAME in module else module[MODULE]


# applies named arguments to string templates
def _apply_arguments_to_templates(template: str, arguments: {}) -> str:
    # applies arguments to template
    result = template % arguments

    # store the last state of result
    last = result

    # continues applying arguments recursively until no more arguments remain
    while '%(' in result:
        # applies arguments to template again
        result = result % arguments

        # if there were no changes stop loop
        if last == result:
            break

        # store the last state of result
        last = result

    # return the final result
    return result


def _bdd_test_name(
        given: str,
        should_or_not: bool,
        action: str,
        scenario: str,
        suffix: str | None
) -> str:
    should_or_not = 'be' if should_or_not else 'not_be'
    suffix = '_%s' % suffix.strip() if suffix is not None and not len(suffix.strip()) == 0 else ''

    return f'given_{given}_you_should_{should_or_not}_able_to_{action}_{scenario}{suffix}'


# counts the number of columns of a module for the test doc creation
def _columns_for_module(module: {}, module_mappings: {}) -> int:
    # get the module mappings relevant to a module
    module_mappings = _get_module_mappings(module, module_mappings or {})

    # get the submodules relevant to a module
    submodules = _get_module_submodules(module, module_mappings=module_mappings)

    # if the stage of module is in file, count only one column
    if _get_module_stage(module, submodules) == Stage.IN_FILE:
        return 1

    # otherwise, return the sum of all columns of submodules
    return sum([_columns_for_module(submodule, module_mappings) for submodule in submodules])


# creates and writes the test.doc md file for the subject under test
def _create_test_doc(
        module_name: str,
        modules: list[{}],
        scenarios: {},
        applied: {},
        module_mappings: {},
):
    # create/overwrite tests documentations
    open(TESTS_DOC, 'w')

    # adds the module name as the title of the md document
    append_to_file(TESTS_DOC, lambda: f'# {module_name.capitalize()}')

    # builds the test doc's test matrix
    doc = _create_test_doc_matrix(modules, scenarios, applied, module_mappings)

    # enumerates the test matrix doc line by line
    for (line_number, line) in enumerate(doc):
        # marks the first column bold
        marked = [
            '__%s__' % text if column == 0 and not len(text) == 0 else text
            for (column, text) in enumerate(line)
        ]

        # writes the line of matrix table items separated by pipe to build a md table
        append_to_file(TESTS_DOC, lambda: '|%s|' % ' | '.join(marked))

        # if the first line add the title separator line to md table
        if line_number == 0:
            append_to_file(TESTS_DOC, lambda: '|%s|' % '|'.join((['-'] * len(line))))


# generates the test matrix
def _create_test_doc_matrix(
        modules: list[{}],
        scenarios: {},
        applied: {},
        module_mappings: {},
) -> list[list[str]]:
    # build the document matrix column by column; left to right
    def build_test_matrix(
            lvl_modules: list[{}],
            lvl_scenarios: {},
            lvl_applied: {},
            lvl_module_mappings: {},
            level: int = 0,
            doc: list[list[str]] = None
    ) -> list[list[str]]:
        # initialize an empty doc if one was not created
        doc = doc or []

        # continue build column with module hierarchy while there are more than one layer child modules
        build_column = not all([
            len([True for module in submodules if MODULES not in module]) == 0
            for module in lvl_modules
            for submodules in _get_module_submodules(module, module_mappings=lvl_module_mappings)
        ])

        if build_column:
            # add an empty column every new level, i.e. level is the same as the number of lines in doc
            if level == len(doc):
                doc.append([''])

            # build a level for each submodule
            for module in lvl_modules:
                # count the expected number of columns for module
                columns = _columns_for_module(module, lvl_module_mappings)
                module_name = get_module_name(module)

                # get the doc line for the current level
                level_line = doc[level]
                # convert the module name to a title and add it as a column to the current level of the document
                level_line.append(' '.join([part.capitalize() for part in module_name.split('_')]))
                # add a blank column for the remaining anticipated columns for the current module
                [level_line.append('') for _ in range(columns - 1)]

                # get the next level of arguments
                nxt_submodules = _get_module_submodules(module, module_mappings=lvl_module_mappings)
                nxt_scenarios = _get_module_scenarios(module, lvl_scenarios)
                nxt_applied = _get_module_applied_scenarios(module_name, module, lvl_applied)
                nxt_module_mappings = _get_module_mappings(module, lvl_module_mappings)

                # build the next level of the current column of the current module
                build_test_matrix(
                    nxt_submodules, nxt_scenarios, nxt_applied,
                    nxt_module_mappings, level + 1, doc
                )
        else:
            # start build scenario levels once the column titles are complete

            # use the ordered labels for the scenarios
            ordered_labels = lvl_scenarios[ORDERED_LABELS]
            # use the module formatting values
            formatting = lvl_scenarios[FORMATTING] if FORMATTING in lvl_scenarios else None

            # build each scenario level for the current column
            for scenario_label in ordered_labels:
                # get the scenario variant definition
                variant = scenario_label[VARIANT]

                # create a new level and add the scenario label the first time the level is being built
                if level == len(doc):
                    doc.append([scenario_label[LABEL]])

                # get the level being created
                level_line = doc[level]

                # gets the applied scenario variant for the current module
                def get_applied(apply: {}, module: str) -> str:
                    # determine if the there is formatting for the current module
                    if formatting is None or module not in formatting:
                        # if there is no formatting defined for the module use the applied scenario variant
                        return apply
                    else:
                        # construct applied arguments for formatting, including the module name
                        # and format the applied scenario variant
                        return formatting[module] % {
                            **apply,
                            'module_name': module
                        }

                # creates a label with everything that applies, if any
                applies = ' ; '.join([
                    get_applied(lvl_applied[module][variant], module)
                    for module in [get_module_name(module) for module in lvl_modules]
                    if module in lvl_applied and variant in lvl_applied[module]
                ])

                # add applies if there is something that applies otherwise add indicator to the contrary
                level_line.append(applies if not len(applies) == 0 else '---')

                # build the next level
                level += 1

        return doc

    # start building the test matrix
    return build_test_matrix(modules, scenarios, applied, module_mappings)


# generates and appends all test scenarios for module to test file
def _generate_test_scenarios(
        module_test: {},
        scenarios: {},
        applied: {},
        action: str,
        file_name: str
) -> None:
    # checks if test definition has all the requisite fields, i.e. is it my duck
    def is_complete_test() -> bool:
        return TEST_ACTUAL in module_test and \
            TEST_EXPECTED in module_test and \
            TEST_GIVEN in module_test and \
            TEST_SUT in module_test and \
            VARIANTS in scenarios

    # generate and append the test to the test file
    def generate(scenario_name: str) -> None:
        # test arguments for generated scenario test
        scenario_test_args = {
            **test_args,  # arguments from test definition
            **applied[scenario_name],  # arguments from applied scenario variant
            'sut': sut  # the subject under test
        }

        # generate the BDD test name
        test_name = _bdd_test_name(given, should_or_not, action, scenario_name, suffix)
        # get the scenario variant
        variant = scenario_variants[scenario_name]

        # generate all subject under test inputs defined in scenario variant
        sut_input = ' '.join([
            # generate the input code for each input in the scenario variant
            'let %s = %s;' % (input_name, variant[input_name])
            # for each input name in scenario variant
            for input_name in variant
        ])

        # get post test code
        post_test = '%s\n' % module_test[TEST_POST] if TEST_POST in module_test else ''

        # generate actual test and append it to test file
        append_to_file(
            file_name,
            # generate test code and apply scenario test arguments
            lambda: _apply_arguments_to_templates(f'''\
#[test]
fn {test_name}() {{\
    let sut = {sut};\
    {sut_input}\
    let actual = {actual};\
    let expected = {expected};\n
    assert_eq!(expected, actual);\
    {post_test}\
}}\n''', scenario_test_args
                                                  )
        )

    # only generate tests if test definition contains all requisites
    if not is_complete_test():
        return

    # gather all components of test definition
    action = module_test[TEST_ACTION] or action
    actual = module_test[TEST_ACTUAL]
    expected = module_test[TEST_EXPECTED]
    given = module_test[TEST_GIVEN]
    given = given if isinstance(given, str) else '_'.join(given)
    should_or_not = module_test[TEST_SHOULD] if TEST_SHOULD in module_test else False
    sut = module_test[TEST_SUT]
    suffix = scenarios[SUFFIX] if SUFFIX in scenarios else None
    scenario_variants = scenarios[VARIANTS]
    test_args = module_test[TEST_ARGS] if TEST_ARGS in module_test else {}

    # output any additional prefix-code for test module
    if TEST_CODE in module_test:
        append_to_file(file_name, lambda: '%s\n' % ''.join(module_test[TEST_CODE]))

    # generate all the test scenario variants that apply to this module
    [generate(scenario_name) for scenario_name in scenario_variants if scenario_name in applied]

    # output any additional postfix-code
    if TEST_POST_CODE in module_test:
        append_to_file(file_name, lambda: '%s\n' % ''.join(module_test[TEST_POST_CODE]))


# generate tests for a list of submodules
def _generate_tests_for_submodules(
        submodules: list[{}],
        module_test: {},
        scenarios: {},
        applied: dict | list,
        module_mappings: {},
        level: int,
        test_file: str = None,
        file_level: int = None
):
    # loop through and generate test for each submodule
    for submodule in submodules:
        submodule_name = get_module_name(submodule)

        # don't generate any tests if there aren't any applied test scenario variante
        if not applied == {} and submodule_name not in applied:
            continue

        submodules_mapped = _get_module_mappings(submodule, module_mappings)

        generate_tests(
            submodule,
            module_test,
            submodules_mapped,
            scenarios,
            applied,
            level + 1,
            test_file,
            file_level + 1 if file_level is not None else None
        )


# get all the test scenario variants that apply to a module
def _get_module_applied_scenarios(module_name: str, module: {}, parent_applied: {}) -> {}:
    # get applied modules defined in module or use parent applied definitions
    applied = module[APPLIED_SCENARIOS] if APPLIED_SCENARIOS in module else parent_applied or {}

    # if a module has applied test scenario variants return it
    if module_name in applied:
        return applied[module_name]

    # check if there are additional applied scenarios to extend applied scenarios
    if APPLIED_SCENARIOS_PLUS in module:
        # additional applied scenarios
        additional_applied: {} = applied[APPLIED_SCENARIOS_PLUS]

        if module_name in additional_applied:
            return additional_applied[module_name]

        # add additional applied scenarios to applied scenarios
        for module_name in additional_applied:
            applied[module_name] = additional_applied[module_name]

        # def merge(mod_name):
        #     applied[mod_name] = additional_applied[mod_name]
        #
        # [merge(module_name) for module_name in additional_applied]

    # if a module has applied test scenario variants return it, otherwise return all applied
    return applied[module_name] if module_name in applied else applied


# get the mappings defined for a module
def _get_module_mappings(module: {}, parent_mappings: {}) -> {}:
    # use module mappings of module, otherwise use module mappings from parent
    module_mappings = module[MAPPINGS] if MAPPINGS in module else parent_mappings or {}

    # check if there are additional module mappings to extend module mappings
    if MAPPINGS_PLUS in module:
        # additional module mappings
        additional_mappings: {} = module[MAPPINGS_PLUS]

        # add additional module mappings to module mappings
        for module_name in additional_mappings:
            module_mappings[module_name] = additional_mappings[module_name]

    return module_mappings


# get scenarios defined for a module
def _get_module_scenarios(module: {}, parent_scenarios: {}) -> {}:
    # use scenarios of module, otherwise use scenarios from parent
    scenarios = module[SCENARIOS] if SCENARIOS in module else parent_scenarios or {}

    # check if there are additional definitions to extend scenarios
    if SCENARIOS_PLUS in module:
        # additional scenarios
        additional_scenarios: {} = module[SCENARIOS_PLUS]

        # add additional scenarios to module scenarios
        for scenario in additional_scenarios:
            scenarios[scenario] = additional_scenarios[scenario]

    return scenarios


# determine the stage of a module from its hierarchy
def _get_module_stage(module: {}, submodules: list[{}]) -> Stage:
    # check if module is embedded in a file
    if NAME in module:
        return Stage.IN_FILE

    # check if module is defined in a folder, any MODULE in submodules
    if any(MODULE in sub_module for sub_module in submodules) if not len(submodules) == 0 else False:
        return Stage.FOLDER

    # otherwise tests are in the current file
    return Stage.FILE


# get submodules of a module
def _get_module_submodules(
        module: {},
        mappings: {} = None,
        module_mappings: {} = None
) -> list[{}]:
    # self-sufficient mapped module resolver, works with either provided mappings or module mappings
    mappings = mappings or _get_module_mappings(module, module_mappings or {})

    # gets submodules of current module, if any
    submodules = module[MODULES] if MODULES in module else []

    # resolve module mappings if any
    return list(map(
        # gets a mapped module if module is a mapping key (str)
        lambda module_or_name:
        mappings[module_or_name]
        if isinstance(module_or_name, str) and module_or_name in mappings
        else module_or_name,

        [submodule for submodule in submodules]
    ))


# gets the test as it is defined for the module
# tests are build hierarchically from a parent test
# given and test arguments accumulate
# and all other fields override any parent provided field
def _get_module_test(module: {}, parent_test: {}) -> {}:
    # list of fields that should not propagate
    dont_propagate: list[str] = [TEST_GIVEN, TEST_ARGS]

    # if test defined in module, combine w/parent test
    if TEST in module:
        module_test = dict(module[TEST])

        # copy all propagated fields from parent test
        for field in parent_test:
            if field not in dont_propagate:
                module_test[field] = parent_test[field]

        # if parent test defines a given, added it to module test
        if TEST_GIVEN in parent_test:
            parent_given = parent_test[TEST_GIVEN]
            # convert to list of given if necessary
            parent_given = [parent_given] if isinstance(parent_given, str) else parent_given

            if TEST_GIVEN not in module_test:
                # add given to module test if one is not defined
                module_test[TEST_GIVEN] = parent_given
            else:
                # otherwise extend given of module test
                # get defined module test given
                module_given = module_test[TEST_GIVEN]

                # handle str or list given variants
                if isinstance(module_given, str):
                    module_test[TEST_GIVEN] = [module_given, *parent_given]
                else:
                    module_test[TEST_GIVEN] = [*module_given, *parent_given]

        # parent test defines test data, add it to module test
        if TEST_ARGS in parent_test:
            parent_data = parent_test[TEST_ARGS]

            if TEST_ARGS not in module_test:
                # add data to module test if one is not defined
                module_test[TEST_ARGS] = parent_data
            else:
                # otherwise extend data of module test
                module_test[TEST_ARGS] = {
                    **module_test[TEST_ARGS],
                    **parent_data
                }

        return module_test
    else:
        # otherwise, use parent test
        return dict(parent_test)


# registers a rust module in the correct project file
def _register_rs_module(module_name: str, location: str) -> None:
    # constructs the mod.rs path based on the expected location, i.e. current or parent dir
    mod_rs = os.path.join(location, MOD_RS)

    # if the mod.rs file does not exist, create it
    if not os.path.exists(mod_rs):
        open(mod_rs, 'x')

    # if mod.rs is not a file, its an exception
    if not os.path.isfile(mod_rs):
        raise Exception("'%s' is not a file, cannot add mod '%s'" % (mod_rs, module_name))

    # defined the module declaration in rust
    mod_declaration = 'mod %s;' % module_name

    # skip if module declaration is already in the module file
    if file_contains(mod_rs, mod_declaration):
        return

    # otherwise append the module declaration to appropriate mod.rs
    append_to_file(mod_rs, lambda: mod_declaration)


# determine all the stages of a list of submodules
def _submodule_stages(
        submodules: list[{}],
        module_mappings: {},
) -> list[Stage]:
    # iterate and determine all the stages in each submodule
    # if it is not the last module in the test definition hierarchy
    return [
        _get_module_stage(submodule, _get_module_submodules(submodule, module_mappings=module_mappings))
        for submodule in submodules if MODULES in submodule
    ]


# validates the definition of a module
# it must have either a name or module field, but not both
def _validate_module(module):
    # module must be labeled with a 'name' or 'module' field
    if NAME not in module and MODULE not in module:
        raise ValueError(
            "%s test module is not labeled with a '%s' or '%s' field"
            % (module.capitalize(), NAME, MODULE)
        )

    # module can only be labeled with a 'name' or 'module' field, not both
    if NAME in module and MODULE in module:
        raise ValueError(
            "%s test module can only be label by a '%s' or '%s' field, not both"
            % (module.capitalize(), NAME, MODULE)
        )
