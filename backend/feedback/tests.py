from unittest import mock

from django.test import SimpleTestCase

from courses.models import RubricCriterion
from courses.models import TestCase as TestCaseModel  # django's TestCase is used below
from execution.runner import RunOutcome
from execution.services import execute_submission
from execution.tests import ExecutionTestCase
from submissions.models import Submission

from .models import Feedback
from .rules import (
    AttemptEvidence,
    ResultEvidence,
    build_feedback,
    diagnose_output,
    parse_compile_error,
    parse_runtime_error,
)

PYTHON_ZERO_DIVISION = '''Traceback (most recent call last):
  File "/work/main.py", line 3, in <module>
    print(a // b)
          ~~^^~~
ZeroDivisionError: integer division or modulo by zero
'''

PYTHON_VALUE_ERROR_WITH_SECRET = '''Traceback (most recent call last):
  File "/work/main.py", line 1, in <module>
ValueError: invalid literal for int() with base 10: 'SECRET-IN'
'''


def result(name='Example', passed=True, error_type=None, hidden=False, **fields):
    defaults = {
        'test_result_id': fields.pop('test_result_id', abs(hash(name)) % 10_000),
        'name': name,
        'is_hidden': hidden,
        'passed': passed,
        'error_type': error_type,
        'stdin': '2 3\n',
        'expected': '5\n',
        'actual': '5\n' if passed else '',
        'stderr': '',
        'time_limit_ms': 2000,
    }
    return ResultEvidence(**(defaults | fields))


def evidence(results, depth='detailed', language='python', **fields):
    return AttemptEvidence(language=language, depth=depth, results=results, attempt_number=1, **fields)


def kinds(draft):
    return [item.kind for item in draft.items]


def messages(draft):
    return ' '.join(item.message for item in draft.items) + ' ' + draft.summary


class ParsingTests(SimpleTestCase):
    def test_cpp_and_java_compiler_messages(self):
        cpp = parse_compile_error('cpp', "main.cpp: In function 'int main()':\nmain.cpp:4:12: error: 'x' was not declared")
        java = parse_compile_error('java', "Main.java:7: error: ';' expected\n        int a = 1\n")

        self.assertEqual((cpp.line, cpp.message), (4, "'x' was not declared"))
        self.assertEqual((java.line, java.message), (7, "';' expected"))

    def test_python_traceback_gives_exception_and_line(self):
        info = parse_runtime_error('python', PYTHON_ZERO_DIVISION)

        self.assertEqual((info.exception, info.line, info.category), ('ZeroDivisionError', 3, 'runtime_error'))

    def test_python_syntax_error_is_its_own_category(self):
        info = parse_runtime_error('python', '  File "/work/main.py", line 2\n    print(\n         ^\nSyntaxError: \'(\' was never closed')

        self.assertEqual((info.category, info.line), ('syntax_error', 2))

    def test_java_and_javascript_exceptions(self):
        java = parse_runtime_error(
            'java',
            'Exception in thread "main" java.lang.ArithmeticException: / by zero\n\tat Main.main(Main.java:5)',
        )
        js = parse_runtime_error(
            'javascript', "/work/main.js:2\nfoo();\n^\n\nReferenceError: foo is not defined\n    at Object.<anonymous>"
        )

        self.assertEqual((java.exception, java.line), ('ArithmeticException', 5))
        self.assertEqual((js.exception, js.line), ('ReferenceError', 2))


class DiagnoseOutputTests(SimpleTestCase):
    def test_common_mistakes_are_named(self):
        cases = [
            ('5\n', '', 'empty_output'),
            ('Hello World\n', 'hello world\n', 'letter_case'),
            ('1 2 3\n', '1  2 3\n', 'spacing'),
            ('5\n', 'Enter two numbers: 5\n', 'extra_text'),
            ('2.50\n', '2.5\n', 'number_format'),
            ('1\n2\n', '1\n', 'line_count'),
            ('5\n', '6\n', 'wrong_value'),
        ]
        for expected, actual, category in cases:
            with self.subTest(category):
                self.assertEqual(diagnose_output(expected, actual, show_values=True)[0], category)

    def test_values_are_quoted_only_when_asked(self):
        _, detailed = diagnose_output('5\n', '6\n', show_values=True)
        _, guided = diagnose_output('5\n', '6\n', show_values=False)

        self.assertIn('"5"', detailed)
        self.assertNotIn('"5"', guided)


class BuildFeedbackTests(SimpleTestCase):
    def test_no_results_gives_no_feedback(self):
        self.assertIsNone(build_feedback(evidence([])))

    def test_all_passing(self):
        draft = build_feedback(evidence([result('A'), result('B')]))

        self.assertEqual(draft.summary, 'All 2 tests pass.')
        self.assertEqual(kinds(draft), ['strength', 'next_step'])

    def test_every_draft_ends_with_exactly_one_next_step(self):
        drafts = [
            build_feedback(evidence([result('A', False, 'wrong_answer', actual='6\n')])),
            build_feedback(evidence([result('A', False, 'time_limit')])),
            build_feedback(evidence([result('A', False, 'compile_error', stderr='x')], language='cpp')),
        ]
        for draft in drafts:
            self.assertEqual(kinds(draft).count('next_step'), 1)
            self.assertEqual(kinds(draft)[-1], 'next_step')

    def test_compile_error_is_reported_once_with_its_line(self):
        stderr = "main.cpp:2:5: error: expected ';'"
        draft = build_feedback(
            evidence(
                [result('A', False, 'compile_error', stderr=stderr), result('B', False, 'compile_error', stderr=stderr)],
                language='cpp',
            )
        )

        [issue] = [item for item in draft.items if item.kind == 'issue']
        self.assertEqual((issue.line_start, issue.error_category), (2, 'compile_error'))
        self.assertIn("expected ';'", issue.message)

    def test_same_crash_in_many_tests_is_grouped(self):
        crash = {'passed': False, 'error_type': 'runtime_error', 'stderr': PYTHON_ZERO_DIVISION}
        draft = build_feedback(evidence([result('A', **crash), result('B', **crash), result('C', **crash)]))

        [issue] = [item for item in draft.items if item.kind == 'issue']
        self.assertIn('3 tests crashed the same way', issue.message)
        self.assertIn('ZeroDivisionError (a division by zero) on line 3', issue.message)
        self.assertEqual(draft.items[-1].message, 'Fix the error on line 3.')

    def test_public_wrong_answer_explains_the_difference(self):
        draft = build_feedback(evidence([result('Small', False, 'wrong_answer', actual='6\n')]))

        self.assertIn('Output line 1 should be "5" but was "6"', messages(draft))

    def test_hidden_failures_after_passing_examples_point_to_edge_cases(self):
        draft = build_feedback(
            evidence([result('Example'), result('Hidden test 1', False, 'wrong_answer', hidden=True, actual='9\n')])
        )

        self.assertIn('edge cases', messages(draft))

    def test_hidden_test_data_never_appears(self):
        secret = {'stdin': 'SECRET-IN\n', 'expected': 'SECRET-EXP\n', 'hidden': True, 'passed': False}
        draft = build_feedback(
            evidence(
                [
                    result('Hidden test 1', error_type='wrong_answer', actual='SECRET-OUT\n', **secret),
                    result(
                        'Hidden test 2', error_type='runtime_error', stderr=PYTHON_VALUE_ERROR_WITH_SECRET, **secret
                    ),
                    result('Hidden test 3', error_type='time_limit', actual='SECRET-OUT', **secret),
                ]
            )
        )

        self.assertNotIn('SECRET', messages(draft))
        # The exception type and the line are the student's own code, so they stay.
        self.assertIn('ValueError', messages(draft))
        self.assertIn('line 1', messages(draft))

    def test_public_crash_message_is_quoted_only_in_detailed(self):
        crash = result('A', False, 'runtime_error', stderr=PYTHON_ZERO_DIVISION)

        detailed = build_feedback(evidence([crash], depth='detailed'))
        guided = build_feedback(evidence([crash], depth='guided'))

        self.assertIn('integer division or modulo by zero', messages(detailed))
        self.assertNotIn('integer division or modulo by zero', messages(guided))

    def test_hint_depth_gives_only_the_next_step(self):
        draft = build_feedback(evidence([result('A'), result('B', False, 'wrong_answer', actual='6\n')], depth='hint'))

        self.assertEqual(kinds(draft), ['next_step'])

    def test_progress_since_the_previous_attempt_is_a_strength(self):
        draft = build_feedback(evidence([result('A'), result('B')], previous_passed=1))

        self.assertIn('1 more test(s) pass than in your previous attempt', messages(draft))

    def test_criterion_whose_tests_all_pass_is_a_strength(self):
        draft = build_feedback(
            evidence(
                [
                    result('A', criterion_id=7, criterion_title='Correct sum'),
                    result('B', False, 'wrong_answer', actual='6\n', criterion_id=8, criterion_title='Big numbers'),
                ]
            )
        )

        strengths = [item for item in draft.items if item.kind == 'strength']
        self.assertIn(7, [item.criterion_id for item in strengths])
        self.assertNotIn(8, [item.criterion_id for item in strengths])

    def test_untested_criteria_become_the_next_step_when_all_pass(self):
        draft = build_feedback(evidence([result('A')], untested_criteria=['Readable code']))

        self.assertIn('"Readable code"', draft.items[-1].message)


@mock.patch('execution.services.run_code')
class StoredFeedbackTests(ExecutionTestCase):
    def outcome(self, stdout='', **fields):
        return RunOutcome(stdout=stdout, stderr=fields.pop('stderr', ''), exit_code=fields.pop('exit_code', 0), **fields)

    def attempts(self):
        self.client.force_login(self.student)
        return self.client.get(self.url())

    def test_feedback_is_stored_after_the_tests_run(self, run_code):
        run_code.side_effect = [self.outcome('5\n'), self.outcome('7\n')]
        submission = self.attempt()

        execute_submission(submission.id)

        feedback = Feedback.objects.get(submission=submission)
        self.assertEqual((feedback.source, feedback.summary), ('rules', '1 of 2 tests pass.'))
        self.assertEqual(feedback.evidence_version, 'rules-v1')
        self.assertTrue(feedback.items.filter(kind='next_step').exists())

    def test_api_shows_feedback_without_hidden_data(self, run_code):
        run_code.side_effect = [
            self.outcome('5\n'),
            self.outcome('SECRET-OUT\n', stderr=PYTHON_VALUE_ERROR_WITH_SECRET, exit_code=1),
        ]
        execute_submission(self.attempt().id)

        response = self.attempts()

        feedback = response.json()[0]['feedback']
        self.assertEqual(feedback['source'], 'rules')
        self.assertEqual(feedback['items'][-1]['kind'], 'next_step')
        # The hidden test's name, input, expected output, output and stderr.
        self.assertNotIn('SECRET', response.content.decode())

    def test_items_link_to_the_criterion_and_the_code_line(self, run_code):
        criterion = RubricCriterion.objects.create(assignment=self.assignment, title='Correct sum', max_points=5)
        TestCaseModel.objects.filter(id=self.public.id).update(criterion=criterion)
        run_code.side_effect = [self.outcome(stderr=PYTHON_ZERO_DIVISION, exit_code=1), self.outcome('x')]
        execute_submission(self.attempt().id)

        crash = Feedback.objects.get().items.get(error_category='runtime_error')

        self.assertEqual((crash.criterion_id, crash.line_start, crash.line_end), (criterion.id, 3, 3))
        self.assertEqual(crash.file.path, 'main.py')
        items = self.attempts().json()[0]['feedback']['items']
        [api_crash] = [item for item in items if item['error_category'] == 'runtime_error']
        self.assertEqual((api_crash['criterion_title'], api_crash['line_start']), ('Correct sum', 3))

    def test_a_feedback_bug_does_not_undo_the_results(self, run_code):
        run_code.return_value = self.outcome('5\n')
        submission = self.attempt()

        with mock.patch('feedback.services.build_feedback', side_effect=RuntimeError('bug')), self.assertLogs(
            'feedback.services', 'ERROR'
        ):
            execute_submission(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.Status.COMPLETED)
        self.assertEqual(submission.test_results.count(), 2)

    def test_no_feedback_without_tests(self, run_code):
        TestCaseModel.objects.all().delete()
        execute_submission(self.attempt().id)

        self.assertFalse(Feedback.objects.exists())
        self.assertIsNone(self.attempts().json()[0]['feedback'])
