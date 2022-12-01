import os
import subprocess
from inspect import getsourcefile
from os.path import abspath

from ppil.ppil._api_response_handler import ExecutionError


def _get_fact_head_and_conditions(fact):
    [head_part, condition_part] = fact.split(':-')
    return [head_part.replace('\n', '').strip(), condition_part.replace('\n', '').strip()]


def _wrap_facts(prolog_program):
    prolog_program = prolog_program.split('.')
    updated_prolog_program = []

    for item in prolog_program:
        if ':-' in item:
            [head_part, condition_part] = _get_fact_head_and_conditions(item)
            fact_arguments = head_part[head_part.index('(')+1:-1]
            result_output_pattern = ' '.join([
                f"~q" for index, item in enumerate(fact_arguments.split(','))
            ])

            updated_prolog_program.append(
                item.replace(
                    condition_part,
                    f'forall(({condition_part}), format("{result_output_pattern}", [{fact_arguments}])), halt'
                )
            )

        else:
            updated_prolog_program.append(item)

    return [item for item in updated_prolog_program if len(item) > 0]


class Executor:
    def __init__(self, json_parser, json_format_checker):
        self._json_parser = json_parser
        self._json_format_checker = json_format_checker
        self._current_directory = None

    def execute_code(self, code):
        if not code.get('query') and not isinstance(code.get('query'), list):
            raise ExecutionError(response='No set query or query is not list.')

        self._set_current_directory()

        prolog_source_path = f"{self._current_directory}/source_script.pl"
        executor_path = f"{self._current_directory}/executor.sh"

        source_code = code['data']
        code_query = code.get('query')
        source_script_file = open(prolog_source_path, 'w+')

        os.chmod(prolog_source_path, 0o700)
        os.chmod(executor_path, 0o700)

        if not isinstance(source_code, str):
            json_data = self._json_format_checker.check_json_format(code)
            source_code = self._json_parser.parse_json(json_data)
            source_code = source_code.replace('\n', '').strip()

        serialized_program = _wrap_facts(source_code)
        serialized_program = '.'.join(serialized_program)

        source_script_file.write(serialized_program)
        source_script_file.close()

        results = []
        for query in code_query:
            execution_result = subprocess.run([
                'swipl', '-q', '-g', query, '-t', 'halt', prolog_source_path
            ], stdout=subprocess.PIPE)
            results.append(execution_result.stdout.decode('utf-8'))

        return results

    def _set_current_directory(self):
        current_directory = abspath(getsourcefile(lambda: 0))
        current_directory = current_directory.split('/')
        self._current_directory = '/'.join(current_directory[:-1])
