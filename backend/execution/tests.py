import shutil
import subprocess
import unittest
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase

from courses.models import TestCase as TestCaseModel  # django's TestCase is used below
from submissions.models import Submission, SubmissionFile, TestResult
from submissions.tests import SubmissionTestCase

from .grading import COMPILE_TOO_SLOW, judge, normalize_output
from .runner import LANGUAGES, RunnerUnavailable, RunOutcome, run_code
from .services import execute_submission

Status = Submission.Status
ErrorType = TestResult.ErrorType


def outcome(stdout='', **fields):
    return RunOutcome(stdout=stdout, stderr=fields.pop('stderr', ''), exit_code=fields.pop('exit_code', 0), **fields)


class GradingTests(SimpleTestCase):
    def test_line_end_spaces_and_final_blank_lines_are_ignored(self):
        self.assertEqual(normalize_output('3  \r\n4\n\n\n'), ['3', '4'])

    def test_leading_spaces_and_inner_blank_lines_matter(self):
        self.assertNotEqual(normalize_output(' 3'), normalize_output('3'))
        self.assertNotEqual(normalize_output('3\n\n4'), normalize_output('3\n4'))

    def test_matching_output_passes(self):
        verdict = judge(outcome('5', runtime_ms=12), '5\n')

        self.assertTrue(verdict.passed)
        self.assertIsNone(verdict.error_type)
        self.assertEqual(verdict.runtime_ms, 12)

    def test_verdicts(self):
        cases = [
            (outcome('6\n'), ErrorType.WRONG_ANSWER),
            (outcome('5\n', exit_code=1), ErrorType.RUNTIME_ERROR),
            (outcome('', exit_code=137), ErrorType.MEMORY_LIMIT),
            (outcome('5\n', exit_code=None, timed_out=True), ErrorType.TIME_LIMIT),
            (outcome('5\n', output_truncated=True), ErrorType.OUTPUT_LIMIT),
            (outcome(stderr='error: x', exit_code=200, compile_failed=True), ErrorType.COMPILE_ERROR),
        ]
        for run, expected in cases:
            with self.subTest(expected):
                verdict = judge(run, '5\n')
                self.assertFalse(verdict.passed)
                self.assertEqual(verdict.error_type, expected)

    def test_compile_error_keeps_the_compiler_message(self):
        verdict = judge(outcome(stderr='main.cpp:1: error', exit_code=200, compile_failed=True), '')

        self.assertEqual(verdict.error_output, 'main.cpp:1: error')
        self.assertIsNone(verdict.actual_output)

    def test_slow_compile_is_a_compile_error(self):
        verdict = judge(outcome(exit_code=None, compile_timed_out=True), '')

        self.assertEqual((verdict.error_type, verdict.error_output), (ErrorType.COMPILE_ERROR, COMPILE_TOO_SLOW))


class ExecutionTestCase(SubmissionTestCase):
    def setUp(self):
        super().setUp()
        self.public = self.add_test('Small numbers', TestCaseModel.Visibility.PUBLIC, '2 3\n', '5\n')
        self.hidden = self.add_test('Negative SECRET', TestCaseModel.Visibility.HIDDEN, 'SECRET-IN\n', 'SECRET-EXP\n')

    def add_test(self, name, visibility, stdin, expected, assignment=None):
        return TestCaseModel.objects.create(
            assignment=assignment or self.assignment,
            name=name,
            visibility=visibility,
            stdin_input=stdin,
            expected_output=expected,
        )

    def attempt(self, language='python', code='print(5)', status=Status.QUEUED):
        submission = Submission.objects.create(
            assignment=self.assignment, student=self.student, attempt_number=1, status=status
        )
        path = {'python': 'main.py', 'html': 'index.html', 'cpp': 'main.cpp'}[language]
        SubmissionFile.objects.create(submission=submission, path=path, content=code, is_entry_point=True)
        return submission


@mock.patch('execution.services.run_code')
class ExecuteSubmissionTests(ExecutionTestCase):
    def test_every_test_is_run_and_stored(self, run_code):
        run_code.side_effect = [outcome('5\n', runtime_ms=30), outcome('SECRET-OUT\n', stderr='warn', runtime_ms=40)]
        submission = self.attempt(code='print(5)')

        execute_submission(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.status, Status.COMPLETED)
        run_code.assert_any_call('python', 'print(5)', '2 3\n', 2000)
        public, hidden = submission.test_results.order_by('test_case_id')
        self.assertTrue(public.passed)
        self.assertEqual((hidden.passed, hidden.error_type), (False, ErrorType.WRONG_ANSWER))
        self.assertEqual((hidden.actual_output, hidden.error_output), ('SECRET-OUT\n', 'warn'))

    def test_runner_failure_marks_the_attempt_failed(self, run_code):
        run_code.side_effect = RunnerUnavailable('docker is down')
        submission = self.attempt()

        execute_submission(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.status, Status.FAILED)
        self.assertFalse(TestResult.objects.exists())

    def test_attempt_not_queued_is_skipped(self, run_code):
        submission = self.attempt(status=Status.RUNNING)

        execute_submission(submission.id)

        run_code.assert_not_called()

    def test_html_is_not_run(self, run_code):
        submission = self.attempt(language='html', code='<p>Hi</p>')

        execute_submission(submission.id)

        submission.refresh_from_db()
        run_code.assert_not_called()
        self.assertEqual(submission.status, Status.COMPLETED)

    def test_rerun_replaces_old_results(self, run_code):
        run_code.return_value = outcome('5\n')
        submission = self.attempt()
        execute_submission(submission.id)
        Submission.objects.filter(id=submission.id).update(status=Status.QUEUED)

        execute_submission(submission.id)

        self.assertEqual(submission.test_results.count(), 2)

    def test_assignment_without_tests_completes_with_no_results(self, run_code):
        TestCaseModel.objects.all().delete()
        submission = self.attempt()

        execute_submission(submission.id)

        submission.refresh_from_db()
        self.assertEqual(submission.status, Status.COMPLETED)
        run_code.assert_not_called()


class QueueingTests(ExecutionTestCase):
    @mock.patch('submissions.services.enqueue_submission')
    def test_attempt_is_queued_after_it_is_saved(self, enqueue):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.submit(self.student)

        enqueue.assert_called_once_with(response.json()['id'])

    @mock.patch('execution.tasks.run_submission.delay', side_effect=ConnectionError('redis is down'))
    def test_broker_outage_keeps_the_attempt_queued(self, delay):
        # assertLogs is outermost: the callbacks run when the inner block ends.
        with self.assertLogs('execution.tasks', 'ERROR'), self.captureOnCommitCallbacks(execute=True):
            response = self.submit(self.student)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Submission.objects.get().status, Status.QUEUED)

    @mock.patch('execution.management.commands.requeue_submissions.enqueue_submission')
    def test_requeue_command_resends_queued_and_failed_attempts(self, enqueue):
        failed = self.attempt(status=Status.FAILED)

        call_command('requeue_submissions', stdout=StringIO())
        enqueue.assert_not_called()
        call_command('requeue_submissions', '--failed', stdout=StringIO())

        enqueue.assert_called_once_with(failed.id)
        failed.refresh_from_db()
        self.assertEqual(failed.status, Status.QUEUED)


class StudentResultsApiTests(ExecutionTestCase):
    def store(self, submission, test, **fields):
        return TestResult.objects.create(submission=submission, test_case=test, **fields)

    def attempts(self):
        self.client.force_login(self.student)
        return self.client.get(self.url())

    def test_public_result_shows_output_and_hidden_shows_only_the_verdict(self):
        submission = self.attempt(status=Status.COMPLETED)
        self.store(submission, self.public, passed=True, actual_output='5\n', runtime_ms=20)
        self.store(
            submission,
            self.hidden,
            passed=False,
            error_type=ErrorType.RUNTIME_ERROR,
            actual_output='SECRET-OUT',
            error_output='Traceback: SECRET-IN',
        )

        response = self.attempts()

        [attempt] = response.json()
        self.assertEqual((attempt['passed_count'], attempt['test_count']), (1, 2))
        public, hidden = attempt['results']
        self.assertEqual((public['test_name'], public['actual_output']), ('Small numbers', '5\n'))
        self.assertEqual(public['expected_output'], '5\n')
        self.assertEqual(hidden['test_name'], 'Hidden test 1')
        self.assertTrue(hidden['is_hidden'])
        self.assertEqual(hidden['error_type'], 'runtime_error')
        for field in ('stdin_input', 'expected_output', 'actual_output', 'error_output'):
            self.assertIsNone(hidden[field])
        self.assertNotIn('SECRET', response.content.decode())

    def test_compiler_message_is_shown_even_for_hidden_tests(self):
        submission = self.attempt(status=Status.COMPLETED)
        self.store(submission, self.hidden, passed=False, error_type=ErrorType.COMPILE_ERROR, error_output='bad syntax')

        [attempt] = self.attempts().json()

        self.assertEqual(attempt['results'][0]['error_output'], 'bad syntax')

    def test_queued_attempt_has_no_results_yet(self):
        self.attempt()

        [attempt] = self.attempts().json()

        self.assertEqual((attempt['status'], attempt['results'], attempt['test_count']), ('queued', [], 0))


def _docker_ready():
    if not shutil.which('docker'):
        return False
    try:
        images = subprocess.run(
            ['docker', 'image', 'inspect', *{language.image for language in LANGUAGES.values()}],
            capture_output=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return images.returncode == 0


@unittest.skipUnless(_docker_ready(), 'needs Docker and the runner images (see backend/README.md)')
class RunnerSecurityTests(SimpleTestCase):
    """Runs real hostile code in real containers. Skipped without Docker."""

    def run_python(self, code, stdin='', time_limit_ms=3000):
        return run_code('python', code, stdin, time_limit_ms)

    def test_each_language_reads_input_and_prints(self):
        programs = {
            'python': 'a, b = map(int, input().split())\nprint(a + b)',
            'javascript': 'const [a, b] = require("fs").readFileSync(0, "utf8").split(" ").map(Number);'
            'console.log(a + b);',
            'java': 'import java.util.*; public class Main { public static void main(String[] x) {'
            ' Scanner s = new Scanner(System.in); System.out.println(s.nextInt() + s.nextInt()); } }',
            'cpp': '#include <iostream>\nint main() { int a, b; std::cin >> a >> b; std::cout << a + b; }',
        }
        for language, code in programs.items():
            with self.subTest(language):
                result = run_code(language, code, '2 3\n', 5000)
                self.assertEqual((result.exit_code, result.stdout.strip()), (0, '5'))

    def test_compile_error_returns_the_compiler_message(self):
        result = run_code('cpp', 'int main() { return x; }', '', 2000)

        self.assertTrue(result.compile_failed)
        self.assertIn("'x' was not declared", result.stderr)

    def test_network_is_disabled(self):
        code = (
            'import socket\n'
            'try:\n'
            '    socket.create_connection(("1.1.1.1", 80), timeout=2)\n'
            '    print("connected")\n'
            'except OSError:\n'
            '    print("blocked")'
        )
        self.assertEqual(self.run_python(code).stdout.strip(), 'blocked')

    def test_root_filesystem_is_read_only_and_host_is_not_mounted(self):
        code = (
            'import os\n'
            'try:\n'
            '    open("/escape", "w")\n'
            '    print("wrote")\n'
            'except OSError:\n'
            '    print("read-only")\n'
            'print(os.path.exists("/Users"), os.path.exists("/var/run/docker.sock"))'
        )
        self.assertEqual(self.run_python(code).stdout.split(), ['read-only', 'False', 'False'])

    def test_code_runs_as_an_unprivileged_user(self):
        self.assertEqual(self.run_python('import os; print(os.getuid())').stdout.strip(), '65534')

    def test_worker_secrets_are_not_passed_to_the_container(self):
        with mock.patch.dict('os.environ', {'POSTGRES_PASSWORD': 'worker-secret'}):
            result = self.run_python('import os; print(os.environ.get("POSTGRES_PASSWORD"))')

        self.assertEqual(result.stdout.strip(), 'None')

    def test_infinite_loop_is_stopped_at_the_time_limit(self):
        result = self.run_python('while True: pass', time_limit_ms=1000)

        self.assertTrue(result.timed_out)
        self.assertIsNone(result.exit_code)

    def test_memory_is_limited(self):
        result = self.run_python('x = bytearray(1024 ** 3)')

        self.assertEqual(result.exit_code, 137)

    def test_process_count_is_limited(self):
        code = (
            'import os, time\n'
            'count = 0\n'
            'try:\n'
            '    while True:\n'
            '        if os.fork() == 0:\n'
            '            time.sleep(30)\n'
            '        count += 1\n'
            'except OSError:\n'
            '    print("limited")'
        )
        self.assertEqual(self.run_python(code).stdout.strip(), 'limited')

    def test_endless_output_is_cut_off(self):
        result = self.run_python('import sys\nwhile True: sys.stdout.write("A" * 65536)', time_limit_ms=1000)

        self.assertTrue(result.output_truncated)
        self.assertLessEqual(len(result.stdout), 64 * 1024)

    def test_large_files_cannot_be_written(self):
        code = (
            'try:\n'
            '    open("/tmp/big", "wb").write(b"0" * 32 * 1024 * 1024)\n'
            '    print("wrote")\n'
            'except OSError:\n'
            '    print("limited")'
        )
        self.assertEqual(self.run_python(code).stdout.strip(), 'limited')
