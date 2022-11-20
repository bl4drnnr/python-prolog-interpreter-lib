import re
import pcre
from .interpreter import Conjunction, Variable, Term, TRUE, Rule
from .elem_regex import VARIABLE_REGEX, ARGUMENTS_REGEX


def _parse_functor(rule):
    return rule.split('(')[0]


def _check_if_term_is_rule(term):
    return ':-' in term


def _check_rule_format(rule):
    if '(' not in rule or ')' not in rule:
        raise Exception(f"Invalid rule format: {rule}")


def _split_database_string(input_text):
    split_database = input_text.split('.')
    split_database = [item.strip().replace(" ", "").replace("\n", "") for item in split_database]
    return split_database[:-1]


def _parse_internal_rule(rule):
    TEST_REGEX = r"\((.*)\)"
    data = pcre.findall(ARGUMENTS_REGEX, rule)
    test = pcre.findall(TEST_REGEX, rule)
    filtered_data = [i[1] for i in data]

    res = {}

    for item in filtered_data:
        index = rule.index(item)
        predicate_list = rule[:index].split('(')[:-1][-1]

        found_predicate = ''
        for sym in predicate_list[::-1]:
            if sym in [',', ';']:
                break
            found_predicate += sym
        res[found_predicate[::-1]] = item

    res2 = {}

    for k, v in res.items():
        for item in test:
            if (item == v) and (')' in item or '(' in item):
                break
            else:
                res2[k] = v

    return res2


class Parser(object):
    def __init__(self, input_text):
        self._current_rule = None
        self._variables = None
        self._input_text = input_text
        self._elems = _split_database_string(input_text)

    def parse_rules(self):
        parsed_rules = []

        for elem in self._elems:
            self._variables = {}
            parsed_rules.append(self._parse_rule(elem))

        return parsed_rules

    def parse_query(self):
        self._variables = {}
        query = self._input_text.strip().replace(" ", "")

        functor = _parse_functor(query)
        arguments = self._parse_arguments(query)
        return Term(functor, arguments)

    def _parse_tail(self, tail):
        if not len(tail):
            return None

        # TODO DONT FORGET TO PARSE TAIL
        parsed_tail = []
        split_tail = tail.split('),')

        for item in split_tail:
            if '(' in item and ')' not in item:
                parsed_tail.append(item + ')')
            else:
                parsed_tail.append(item)

        tail_terms = [self._parse_term(item) for item in parsed_tail]
        return Conjunction(tail_terms)

    def _parse_term(self, rule):
        try:
            [head, tail] = rule.split(':-')
        except (Exception,):
            head = rule
            tail = []

        functor = _parse_functor(head)
        arguments = self._parse_arguments(head)
        parsed_tail = self._parse_tail(tail)

        return [Term(functor, arguments), parsed_tail] \
            if parsed_tail \
            else Term(functor, arguments)

    def _parse_arguments(self, rule):
        parsed_rule = _parse_internal_rule(rule)
        parsed_arguments = []

        for parsed_rule_key, parsed_rule_value in parsed_rule.items():
            t = parsed_rule_value.split(',')
            for item in t:
                if re.match(VARIABLE_REGEX, item) is not None:
                    if item == "_":
                        parsed_arguments.append(Variable("_"))
                        continue

                    variable = self._variables.get(item)

                    if variable is None:
                        self._variables[item] = Variable(item)
                        variable = self._variables[item]

                    parsed_arguments.append(variable)
                else:
                    if parsed_rule_value is None:
                        parsed_arguments.append(Term(parsed_rule_key))
                    else:
                        parsed_arguments.append(Term(item))

        return parsed_arguments

    def _parse_rule(self, rule):
        term_head = self._parse_term(rule)

        if _check_if_term_is_rule(rule):
            return Rule(term_head[0], term_head[1])
        else:
            return Rule(term_head, TRUE())
