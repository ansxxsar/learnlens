"""Deterministic feedback: fixed rules that explain test results.

Pure functions over plain data, so every message can be traced to its
evidence and tested without a database. This is the fallback that must
always work, with or without AI feedback (AGENTS.md).

Security: a hidden test's input must never reach the student. Its program
output and stderr can echo that input, so for hidden tests the rules use only
the verdict, the exception's type and the line in the student's own code,
never the exception message or any output.
"""

import re
from dataclasses import dataclass, field

from execution.grading import normalize_output

# Bump when the rules or their evidence change, so stored feedback shows which
# rules produced it (feedback.evidence_version).
EVIDENCE_VERSION = 'rules-v1'

# Wrong answers explained one by one before the rest are grouped.
MAX_DETAILED_TESTS = 3
# Longest output line quoted back to the student.
QUOTE_LIMIT = 80


@dataclass(frozen=True)
class ResultEvidence:
    test_result_id: int
    # As the student sees it: hidden tests are "Hidden test N".
    name: str
    is_hidden: bool
    passed: bool
    error_type: str | None
    stdin: str
    expected: str
    actual: str
    stderr: str
    time_limit_ms: int
    criterion_id: int | None = None
    criterion_title: str | None = None


@dataclass(frozen=True)
class AttemptEvidence:
    language: str
    # "hint", "guided" or "detailed", chosen by the instructor per assignment.
    depth: str
    results: list[ResultEvidence]
    attempt_number: int
    # Passed tests of the previous attempt, if there was one with results.
    previous_passed: int | None = None
    # Rubric criteria that no test checks; the instructor reviews them.
    untested_criteria: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ItemDraft:
    kind: str  # strength, issue or next_step
    message: str
    error_category: str | None = None
    line_start: int | None = None
    criterion_id: int | None = None
    test_result_id: int | None = None


@dataclass(frozen=True)
class FeedbackDraft:
    summary: str
    items: list[ItemDraft]


# Error locations


@dataclass(frozen=True)
class ErrorInfo:
    category: str
    # The exception or compiler message. Never shown for hidden tests.
    message: str | None = None
    exception: str | None = None
    line: int | None = None


COMPILER_ERRORS = {
    'cpp': re.compile(r'^main\.cpp:(\d+):(?:\d+:)?\s*(?:fatal )?error:\s*(.+)$', re.M),
    'java': re.compile(r'^Main\.java:(\d+):\s*error:\s*(.+)$', re.M),
}


def parse_compile_error(language, text):
    match = COMPILER_ERRORS.get(language) and COMPILER_ERRORS[language].search(text or '')
    if not match:
        return ErrorInfo('compile_error', message=None)
    return ErrorInfo('compile_error', message=match.group(2).strip(), line=int(match.group(1)))


PYTHON_LINE = re.compile(r'File "(?:/work/)?main\.py", line (\d+)')
PYTHON_EXCEPTION = re.compile(r'^([A-Za-z_][\w.]*(?:Error|Exception|Interrupt|Exit))(?::\s*(.*))?$')
JS_LINE = re.compile(r'(?:/work/)?main\.js:(\d+)')
JS_EXCEPTION = re.compile(r'^(?:Uncaught\s+)?([A-Za-z]*Error)(?::\s*(.*))?$')
JAVA_EXCEPTION = re.compile(r'Exception in thread "main" ([\w.$]+)(?::\s*(.*))?')
JAVA_LINE = re.compile(r'at Main\.[\w$<>]+\(Main\.java:(\d+)\)')

SYNTAX_EXCEPTIONS = {'SyntaxError', 'IndentationError', 'TabError'}


def parse_runtime_error(language, stderr):
    stderr = stderr or ''
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    exception = message = line = None

    if language == 'python':
        for text in reversed(lines):
            if match := PYTHON_EXCEPTION.match(text):
                exception, message = match.group(1), match.group(2)
                break
        if found := PYTHON_LINE.findall(stderr):
            line = int(found[-1])  # the innermost frame in the student's file
    elif language == 'javascript':
        for text in lines:
            if match := JS_EXCEPTION.match(text):
                exception, message = match.group(1), match.group(2)
                break
        if match := JS_LINE.search(stderr):
            line = int(match.group(1))
    elif language == 'java':
        if match := JAVA_EXCEPTION.search(stderr):
            exception, message = match.group(1).rsplit('.', 1)[-1], match.group(2)
        if match := JAVA_LINE.search(stderr):
            line = int(match.group(1))

    category = 'syntax_error' if exception in SYNTAX_EXCEPTIONS else 'runtime_error'
    return ErrorInfo(category, message=message, exception=exception, line=line)


# Short explanations of common exceptions, in the student's terms.
EXCEPTION_HINTS = {
    'ZeroDivisionError': 'a division by zero',
    'ArithmeticException': 'a division by zero',
    'IndexError': 'an index outside the list or string',
    'ArrayIndexOutOfBoundsException': 'an index outside the array',
    'StringIndexOutOfBoundsException': 'an index outside the string',
    'IndexOutOfBoundsException': 'an index outside the list',
    'KeyError': 'a dictionary key that does not exist',
    'ValueError': 'a value in the wrong format, for example int() on text',
    'NumberFormatException': 'a value in the wrong format, for example parsing text as a number',
    'InputMismatchException': 'input of a different type than the code reads',
    'TypeError': 'a value of the wrong type',
    'NameError': 'a name that is not defined (check spelling)',
    'ReferenceError': 'a name that is not defined (check spelling)',
    'NullPointerException': 'a variable that is null',
    'RecursionError': 'recursion that never stops',
    'StackOverflowError': 'recursion that never stops',
    'RangeError': 'a value outside the allowed range, often endless recursion',
    'EOFError': 'reading more input than the test gives',
    'NoSuchElementException': 'reading more input than the test gives',
    'SyntaxError': 'code that is not valid syntax',
    'IndentationError': 'wrong indentation',
    'TabError': 'mixed tabs and spaces',
}


def _describe_error(info, show_message):
    parts = []
    if info.exception:
        hint = EXCEPTION_HINTS.get(info.exception)
        parts.append(f'{info.exception} ({hint})' if hint else info.exception)
    else:
        parts.append('the program stopped with an error')
    if info.line:
        parts.append(f'on line {info.line}')
    text = ' '.join(parts)
    if show_message and info.message:
        text += f': {_quote(info.message)}'
    return text


# Wrong output


def _quote(text):
    text = text if len(text) <= QUOTE_LIMIT else text[: QUOTE_LIMIT - 1] + '…'
    return f'"{text}"'


def _numbers(lines):
    try:
        return [float(token) for line in lines for token in line.split()]
    except ValueError:
        return None


def diagnose_output(expected, actual, show_values):
    """Names the most likely reason two outputs differ. Public tests only."""
    want, got = normalize_output(expected), normalize_output(actual)

    if not got:
        return 'empty_output', 'Your program printed nothing. Check that it prints the answer.'
    if [line.lower() for line in want] == [line.lower() for line in got]:
        return 'letter_case', 'The output is right except for upper- and lower-case letters.'
    if [''.join(line.split()) for line in want] == [''.join(line.split()) for line in got]:
        return 'spacing', 'The output is right except for the spaces inside lines.'
    if len(want) == len(got) and all(g.endswith(w) and g != w for w, g in zip(want, got) if w):
        return 'extra_text', (
            'Your output has extra text before the answer. Remove prompts such as "Enter a number:"; '
            'the tests only expect the answer.'
        )
    want_numbers, got_numbers = _numbers(want), _numbers(got)
    if want_numbers is not None and want_numbers == got_numbers:
        return 'number_format', 'The numbers are right but formatted differently, for example the decimal places.'
    if len(want) != len(got):
        message = f'Expected {len(want)} line(s) of output, but your program printed {len(got)}.'
        return 'line_count', message
    index = next((i for i, (w, g) in enumerate(zip(want, got)) if w != g), None)
    if index is None:
        return 'wrong_value', 'The output differs from the expected one.'
    if show_values:
        message = f'Output line {index + 1} should be {_quote(want[index])} but was {_quote(got[index])}.'
        return 'wrong_value', message
    return 'wrong_value', f'Output line {index + 1} has a different value than expected.'


# Building the feedback


def _fix_step(line):
    return f'Fix the error on line {line}.' if line else 'Fix the error that stops the program.'


def _failure_issue(result, evidence):
    """One issue for one failed test. Returns (draft, next step text)."""
    detailed = evidence.depth == 'detailed'
    base = {'test_result_id': result.test_result_id, 'criterion_id': result.criterion_id}

    if result.error_type == 'time_limit':
        message = (
            f'"{result.name}" took longer than {result.time_limit_ms} ms. Look for a loop that never ends, '
            'or code that waits for more input than the test gives.'
        )
        return ItemDraft('issue', message, 'time_limit', **base), 'Find the loop that runs too long.'
    if result.error_type == 'memory_limit':
        message = f'"{result.name}" used too much memory. Avoid building very large lists or endless recursion.'
        return ItemDraft('issue', message, 'memory_limit', **base), 'Reduce how much data the program keeps.'
    if result.error_type == 'output_limit':
        message = f'"{result.name}" printed far too much. A print inside a loop may never stop.'
        return ItemDraft('issue', message, 'output_limit', **base), 'Check the prints inside loops.'
    if result.error_type == 'runtime_error':
        info = parse_runtime_error(evidence.language, result.stderr)
        # Hidden tests: type and line only; the message may contain the input.
        description = _describe_error(info, show_message=detailed and not result.is_hidden)
        message = f'"{result.name}" crashed: {description}.'
        step = _fix_step(info.line)
        return ItemDraft('issue', message, info.category, line_start=info.line, **base), step

    # Wrong answer.
    if result.is_hidden:
        message = f'"{result.name}" gives a different output than expected.'
        return ItemDraft('issue', message, 'wrong_answer', **base), None
    category, explanation = diagnose_output(result.expected, result.actual, show_values=detailed)
    message = f'"{result.name}": {explanation}'
    step = f'Compare your output for "{result.name}" with the expected one.'
    return ItemDraft('issue', message, category, **base), step


def build_feedback(evidence: AttemptEvidence) -> FeedbackDraft | None:
    """Feedback for one attempt, or None when no test ran."""
    results = evidence.results
    if not results:
        return None

    total = len(results)
    passed = sum(result.passed for result in results)
    failed = [result for result in results if not result.passed]
    strengths, issues = [], []
    next_step = None

    # A compile error fails every test the same way: one issue is enough.
    compile_failure = next((result for result in failed if result.error_type == 'compile_error'), None)
    if compile_failure:
        info = parse_compile_error(evidence.language, compile_failure.stderr)
        where = f' on line {info.line}' if info.line else ''
        detail = f': {_quote(info.message)}' if info.message and evidence.depth != 'hint' else ''
        issues.append(
            ItemDraft(
                'issue',
                f'Your code does not compile{where}{detail}. No test could run.',
                'compile_error',
                line_start=info.line,
                test_result_id=compile_failure.test_result_id,
            )
        )
        next_step = f'Fix the compiler error{where}, then submit again.'
        summary = 'Your code does not compile yet, so no test could run.'
        return _finish(evidence, summary, strengths, issues, next_step)

    # The same crash in many tests is one problem, reported once.
    crashes = {}
    for result in failed:
        if result.error_type == 'runtime_error':
            info = parse_runtime_error(evidence.language, result.stderr)
            crashes.setdefault((info.exception, info.line), []).append(result)

    explained = set()
    next_steps = []
    for (exception, line), group in crashes.items():
        if len(group) > 1:
            info = ErrorInfo('runtime_error', exception=exception, line=line)
            category = 'syntax_error' if exception in SYNTAX_EXCEPTIONS else 'runtime_error'
            issues.append(
                ItemDraft(
                    'issue',
                    f'{len(group)} tests crashed the same way: {_describe_error(info, show_message=False)}.',
                    category,
                    line_start=line,
                    test_result_id=group[0].test_result_id,
                )
            )
            next_steps.append(_fix_step(line))
            explained.update(result.test_result_id for result in group)

    remaining = [result for result in failed if result.test_result_id not in explained]
    hidden_wrong = [result for result in remaining if result.is_hidden and result.error_type == 'wrong_answer']
    others = [result for result in remaining if result not in hidden_wrong]

    for result in others[:MAX_DETAILED_TESTS]:
        issue, step = _failure_issue(result, evidence)
        issues.append(issue)
        if step:
            next_steps.append(step)
    if len(others) > MAX_DETAILED_TESTS:
        issues.append(ItemDraft('issue', f'{len(others) - MAX_DETAILED_TESTS} more test(s) also fail.'))

    if hidden_wrong:
        public_ok = all(result.passed for result in results if not result.is_hidden)
        count = len(hidden_wrong)
        message = f'{count} hidden test(s) give a different output than expected.'
        if public_ok:
            message += (
                ' The examples pass, so think about edge cases: empty input, zero, negative or very large values.'
            )
        issues.append(ItemDraft('issue', message, 'wrong_answer', test_result_id=hidden_wrong[0].test_result_id))
        next_steps.append('Test your code with edge cases of your own, such as 0, negative and very large values.')

    # Strengths: only what the evidence shows.
    if passed == total:
        strengths.append(ItemDraft('strength', f'All {total} tests pass.'))
    elif passed:
        strengths.append(ItemDraft('strength', f'{passed} of {total} tests pass.'))
    if evidence.previous_passed is not None and passed > evidence.previous_passed:
        gained = passed - evidence.previous_passed
        message = f'Progress: {gained} more test(s) pass than in your previous attempt.'
        strengths.append(ItemDraft('strength', message))
    for criterion_id, title in _criteria_fully_passed(results):
        strengths.append(ItemDraft('strength', f'Every test for "{title}" passes.', criterion_id=criterion_id))

    if next_steps:
        next_step = next_steps[0]
    elif evidence.untested_criteria:
        names = ', '.join(f'"{title}"' for title in evidence.untested_criteria)
        them = 'it' if len(evidence.untested_criteria) == 1 else 'them'
        next_step = f'Your teacher also reviews {names}, which tests cannot check. Make sure your code meets {them}.'
    else:
        next_step = 'All tests pass. Try a few inputs of your own, and make the code easy to read.'

    if passed == total:
        summary = f'All {total} tests pass.'
    else:
        summary = f'{passed} of {total} tests pass.'
    return _finish(evidence, summary, strengths, issues, next_step)


def _criteria_fully_passed(results):
    by_criterion = {}
    for result in results:
        if result.criterion_id is not None:
            by_criterion.setdefault((result.criterion_id, result.criterion_title), []).append(result.passed)
    return [key for key, outcomes in by_criterion.items() if all(outcomes)]


def _finish(evidence, summary, strengths, issues, next_step):
    """Applies the instructor's feedback depth: a hint gives only the next
    step; guided and detailed give everything (detailed also quotes values,
    which the rules above already decided)."""
    items = [] if evidence.depth == 'hint' else [*strengths, *issues]
    if next_step:
        items.append(ItemDraft('next_step', next_step))
    return FeedbackDraft(summary=summary, items=items)
