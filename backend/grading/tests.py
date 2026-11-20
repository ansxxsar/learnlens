from decimal import Decimal

from audit.models import AuditLog
from courses.models import CourseSection, Enrollment, RubricCriterion
from courses.models import TestCase as TestCaseModel  # django's TestCase comes from the base class
from execution.tests import ExecutionTestCase
from submissions.models import Submission, TestResult

from .models import CriterionScore
from .scoring import suggest_points

Status = Submission.Status


class GradingTestCase(ExecutionTestCase):
    """The assignment has a public and a hidden test (weight 1 each) linked to
    "Correct output" (8 points), and "Readable code" (2 points) with no tests."""

    def setUp(self):
        super().setUp()
        self.correct = RubricCriterion.objects.create(
            assignment=self.assignment, title='Correct output', max_points=8, position=0
        )
        self.readable = RubricCriterion.objects.create(
            assignment=self.assignment, title='Readable code', max_points=2, position=1
        )
        TestCaseModel.objects.filter(assignment=self.assignment).update(criterion=self.correct)

    def graded_attempt(self, passed=(True, True), student=None, status=Status.COMPLETED, number=None):
        student = student or self.student
        number = number or Submission.objects.filter(assignment=self.assignment, student=student).count() + 1
        submission = Submission.objects.create(
            assignment=self.assignment, student=student, attempt_number=number, status=status
        )
        submission.files.create(path='main.py', content='print(5)', is_entry_point=True)
        if status == Status.COMPLETED:
            for test, ok in zip([self.public, self.hidden], passed):
                TestResult.objects.create(
                    submission=submission,
                    test_case=test,
                    passed=ok,
                    actual_output='SECRET-OUT' if test == self.hidden else '5\n',
                    error_type=None if ok else 'wrong_answer',
                )
        return submission

    def as_user(self, user):
        self.client.force_login(user)
        return self.client

    def review_url(self, submission):
        return f'/courses/{self.course.id}/assignments/{self.assignment.id}/attempts/{submission.id}'

    def approve(self, submission, scores=None, user=None):
        return self.as_user(user or self.teacher).post(
            self.review_url(submission) + '/grade', {'scores': scores or []}, content_type='application/json'
        )

    def gradebook(self, user=None):
        return self.as_user(user or self.teacher).get(f'/courses/{self.course.id}/gradebook')


class SuggestPointsTests(GradingTestCase):
    def suggest(self, submission):
        criteria = list(self.assignment.rubric_criteria.prefetch_related('test_cases'))
        return suggest_points(criteria, submission.test_results.select_related('test_case'))

    def test_points_follow_the_weight_of_passed_tests(self):
        TestCaseModel.objects.filter(id=self.hidden.id).update(weight=3)

        points = self.suggest(self.graded_attempt(passed=(True, False)))

        self.assertEqual(points[self.correct.id], Decimal('2.00'))  # 8 × 1/4

    def test_untested_criterion_has_no_suggestion(self):
        points = self.suggest(self.graded_attempt())

        self.assertEqual(points[self.correct.id], Decimal('8.00'))
        self.assertIsNone(points[self.readable.id])

    def test_attempt_whose_tests_did_not_run_gets_zero_for_tested_criteria(self):
        points = self.suggest(self.graded_attempt(status=Status.FAILED))

        self.assertEqual(points[self.correct.id], Decimal('0.00'))


class GradebookTests(GradingTestCase):
    def cell(self, body, student):
        return next(cell for cell in body['cells'] if cell['student_id'] == student.id)

    def test_teacher_sees_students_assignments_and_latest_attempt(self):
        self.graded_attempt(passed=(False, False))
        latest = self.graded_attempt(passed=(True, False))

        body = self.gradebook().json()

        self.assertEqual([s['full_name'] for s in body['students']], ['Classmate', 'Student'])
        self.assertEqual(body['assignments'][0]['max_points'], 10)
        cell = self.cell(body, self.student)
        self.assertEqual((cell['latest']['id'], cell['latest']['passed_count']), (latest.id, 1))
        # 4 of the tested 8 points; "Readable code" waits for the teacher.
        self.assertEqual((cell['suggested_points'], cell['needs_review']), (4, True))
        self.assertIsNone(cell['grade'])

    def test_students_without_attempts_have_no_cell(self):
        body = self.gradebook().json()

        self.assertEqual(body['cells'], [])

    def test_no_review_needed_when_every_criterion_is_tested(self):
        self.readable.delete()
        self.graded_attempt(passed=(True, False))

        cell = self.cell(self.gradebook().json(), self.student)

        self.assertEqual((cell['suggested_points'], cell['needs_review']), (4, False))

    def test_only_instructors_of_the_course_can_open_it(self):
        self.assertEqual(self.gradebook(self.student).status_code, 403)
        self.assertEqual(self.gradebook(self.outsider).status_code, 403)

    def test_section_teacher_sees_only_their_section(self):
        section = CourseSection.objects.create(course=self.course, code='01')
        Enrollment.objects.filter(user__in=[self.teacher, self.student]).update(section=section)

        names = [s['full_name'] for s in self.gradebook().json()['students']]

        self.assertEqual(names, ['Student'])

    def test_new_attempt_after_grading_marks_the_grade_outdated(self):
        first = self.graded_attempt()
        self.approve(first, [{'criterion': self.readable.id, 'points': 2}])
        self.graded_attempt()

        grade = self.cell(self.gradebook().json(), self.student)['grade']

        self.assertEqual((grade['submission_id'], grade['points'], grade['is_outdated']), (first.id, 10, True))


class ReviewTests(GradingTestCase):
    def test_teacher_sees_code_hidden_results_and_suggestions(self):
        submission = self.graded_attempt(passed=(True, False))

        body = self.as_user(self.teacher).get(self.review_url(submission)).json()

        self.assertEqual(body['code'], 'print(5)')
        self.assertEqual([r['visibility'] for r in body['results']], ['public', 'hidden'])
        self.assertEqual(body['results'][1]['stdin_input'], 'SECRET-IN\n')
        correct, readable = body['criteria']
        self.assertEqual((correct['suggested_points'], correct['is_tested']), (4, True))
        self.assertEqual((readable['suggested_points'], readable['is_tested']), (None, False))

    def test_students_cannot_open_the_review(self):
        submission = self.graded_attempt()

        self.assertEqual(self.as_user(self.student).get(self.review_url(submission)).status_code, 403)

    def test_section_teacher_cannot_review_another_section(self):
        section = CourseSection.objects.create(course=self.course, code='01')
        Enrollment.objects.filter(user=self.teacher).update(section=section)
        submission = self.graded_attempt()  # the student has no section

        self.assertEqual(self.as_user(self.teacher).get(self.review_url(submission)).status_code, 404)

    def test_attempt_is_not_found_through_another_assignment(self):
        submission = self.graded_attempt()
        other = self.make('Other task')
        url = f'/courses/{self.course.id}/assignments/{other.id}/attempts/{submission.id}'

        self.assertEqual(self.as_user(self.teacher).get(url).status_code, 404)


class ApproveGradeTests(GradingTestCase):
    def student_grade(self):
        attempts = self.as_user(self.student).get(self.url()).json()
        return attempts[0]['grade']

    def test_student_sees_nothing_before_approval(self):
        self.graded_attempt()

        self.assertIsNone(self.student_grade())

    def test_approving_saves_scores_and_shows_the_grade_to_the_student(self):
        submission = self.graded_attempt(passed=(True, False))

        response = self.approve(submission, [{'criterion': self.readable.id, 'points': '1.5'}])

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_graded'])
        correct = CriterionScore.objects.get(criterion=self.correct)
        self.assertEqual((correct.auto_points, correct.final_points, correct.overridden_by), (4, 4, None))
        readable = CriterionScore.objects.get(criterion=self.readable)
        self.assertEqual((readable.auto_points, readable.final_points), (None, Decimal('1.5')))
        self.assertEqual(self.student_grade()['points'], 5.5)
        self.assertEqual(self.student_grade()['max_points'], 10)

    def test_untested_criterion_needs_points(self):
        response = self.approve(self.graded_attempt())

        self.assertEqual(response.status_code, 400)
        self.assertIn(f'score_{self.readable.id}', response.json())
        self.assertFalse(CriterionScore.objects.exists())

    def test_changing_a_suggestion_needs_a_reason(self):
        submission = self.graded_attempt(passed=(True, False))
        scores = [{'criterion': self.correct.id, 'points': 6}, {'criterion': self.readable.id, 'points': 2}]

        without_reason = self.approve(submission, scores)
        scores[0]['reason'] = 'The hidden test expects a format the task did not explain.'
        with_reason = self.approve(submission, scores)

        self.assertEqual(without_reason.status_code, 400)
        self.assertEqual(with_reason.status_code, 200)
        correct = CriterionScore.objects.get(criterion=self.correct)
        self.assertEqual((correct.auto_points, correct.final_points), (4, 6))
        self.assertEqual(correct.overridden_by, self.teacher)
        self.assertIsNotNone(correct.overridden_at)

    def test_points_cannot_exceed_the_maximum(self):
        response = self.approve(self.graded_attempt(), [{'criterion': self.readable.id, 'points': 3}])

        self.assertEqual(response.status_code, 400)

    def test_criterion_of_another_assignment_is_rejected(self):
        other = RubricCriterion.objects.create(assignment=self.make('Other'), title='X', max_points=1)

        response = self.approve(self.graded_attempt(), [{'criterion': other.id, 'points': 1}])

        self.assertEqual(response.status_code, 400)

    def test_attempt_still_running_cannot_be_graded(self):
        response = self.approve(self.graded_attempt(status=Status.RUNNING), [{'criterion': self.readable.id, 'points': 2}])

        self.assertEqual(response.status_code, 400)

    def test_approval_is_audited_without_personal_text(self):
        submission = self.graded_attempt(passed=(True, False))
        self.approve(
            submission,
            [
                {'criterion': self.correct.id, 'points': 5, 'reason': 'Private note about the student'},
                {'criterion': self.readable.id, 'points': 2},
            ],
        )

        log = AuditLog.objects.get()
        self.assertEqual((log.actor, log.action, log.entity_type, log.entity_id), (
            self.teacher, 'grade.approved', 'submissions', submission.id
        ))
        self.assertEqual(log.details['total'], '7.00')
        self.assertNotIn('Private note', str(log.details))

    def test_approving_again_replaces_the_scores_and_keeps_both_logs(self):
        submission = self.graded_attempt()
        self.approve(submission, [{'criterion': self.readable.id, 'points': 1}])
        self.approve(submission, [{'criterion': self.readable.id, 'points': 2}])

        self.assertEqual(CriterionScore.objects.filter(submission=submission).count(), 2)
        self.assertEqual(self.student_grade()['points'], 10)
        self.assertEqual(AuditLog.objects.count(), 2)

    def test_students_cannot_approve(self):
        submission = self.graded_attempt()

        response = self.approve(submission, [{'criterion': self.readable.id, 'points': 2}], user=self.student)

        self.assertEqual(response.status_code, 403)
