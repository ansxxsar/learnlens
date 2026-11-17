from datetime import datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from courses.models import Assignment, Course, Enrollment

from .models import Submission, SubmissionFile
from .selectors import _streak

ALMATY = ZoneInfo('Asia/Almaty')


class SubmissionTestCase(TestCase):
    def setUp(self):
        cache.clear()  # throttle counters live in the cache
        self.course = Course.objects.create(code='CSS105', title='Introduction to Programming', term='Fall 2026')
        self.other_course = Course.objects.create(code='CSS201', title='Data Structures', term='Fall 2026')
        self.student = self.enroll('Student', Enrollment.Role.STUDENT)
        self.classmate = self.enroll('Classmate', Enrollment.Role.STUDENT)
        self.teacher = self.enroll('Teacher', Enrollment.Role.INSTRUCTOR)
        self.outsider = self.enroll('Outsider', Enrollment.Role.STUDENT, course=self.other_course)
        self.assignment = self.make('Hello world')

    def enroll(self, name, role, course=None):
        count = get_user_model().objects.count()
        user = get_user_model().objects.create_user(
            email=f'2200000{count:02d}@sdu.edu.kz', full_name=name, password='test-pass-123'
        )
        Enrollment.objects.create(user=user, course=course or self.course, role=role)
        return user

    def make(self, title, status=Assignment.Status.PUBLISHED, course=None, due_in_days=7):
        return Assignment.objects.create(
            course=course or self.course,
            title=title,
            instructions='Do it.',
            status=status,
            due_at=timezone.now() + timedelta(days=due_in_days),
        )

    def url(self, assignment=None, course=None):
        assignment = assignment or self.assignment
        return f'/courses/{(course or assignment.course).id}/assignments/{assignment.id}/submissions'

    def submit(self, user, assignment=None, course=None, **body):
        self.client.force_login(user)
        payload = {'language': 'python', 'code': 'print("Hello")\n'} | body
        return self.client.post(self.url(assignment, course), payload, content_type='application/json')


class SubmitTests(SubmissionTestCase):
    def test_student_submission_is_stored_and_queued(self):
        response = self.submit(self.student)

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['attempt_number'], 1)
        self.assertEqual(body['status'], 'queued')
        self.assertEqual(body['language'], 'python')
        self.assertEqual(body['code'], 'print("Hello")\n')
        file = SubmissionFile.objects.get()
        self.assertEqual((file.path, file.is_entry_point), ('main.py', True))

    def test_language_decides_the_entry_file(self):
        self.submit(self.student, language='java', code='class Main {}')

        self.assertEqual(SubmissionFile.objects.get().path, 'Main.java')

    def test_attempt_numbers_count_up_per_student(self):
        self.submit(self.student)
        self.submit(self.classmate)

        self.assertEqual(self.submit(self.student).json()['attempt_number'], 2)
        self.assertEqual(Submission.objects.get(student=self.classmate).attempt_number, 1)

    def test_code_whitespace_is_kept(self):
        code = 'def f():\n    return 1\n'

        self.assertEqual(self.submit(self.student, code=code).json()['code'], code)

    def test_empty_code_is_rejected(self):
        response = self.submit(self.student, code='   \n')

        self.assertEqual(response.status_code, 400)
        self.assertIn('code', response.json())
        self.assertFalse(Submission.objects.exists())

    def test_unknown_language_is_rejected(self):
        self.assertEqual(self.submit(self.student, language='rust').status_code, 400)

    def test_oversized_code_is_rejected(self):
        self.assertEqual(self.submit(self.student, code='x' * 50_001).status_code, 400)

    def test_closed_assignment_takes_no_attempts(self):
        closed = self.make('Closed', status=Assignment.Status.CLOSED)

        response = self.submit(self.student, closed)

        self.assertEqual(response.status_code, 400)
        self.assertIn('closed', response.json()['detail'])

    def test_draft_is_not_found(self):
        draft = self.make('Draft', status=Assignment.Status.DRAFT)

        self.assertEqual(self.submit(self.student, draft).status_code, 404)

    def test_instructor_cannot_submit(self):
        self.assertEqual(self.submit(self.teacher).status_code, 403)

    def test_student_of_another_course_cannot_submit(self):
        self.assertEqual(self.submit(self.outsider).status_code, 403)

    def test_assignment_cannot_be_reached_through_another_course(self):
        # The outsider is a student of other_course, so the permission check
        # passes; the lookup must still be scoped to that course.
        response = self.submit(self.outsider, course=self.other_course)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Submission.objects.exists())

    def test_anonymous_request_gets_401(self):
        response = self.client.post(self.url(), {}, content_type='application/json')

        self.assertEqual(response.status_code, 401)

    def test_submissions_are_rate_limited(self):
        for _ in range(20):
            self.submit(self.student)

        self.assertEqual(self.submit(self.student).status_code, 429)


class MyAttemptsTests(SubmissionTestCase):
    def test_student_sees_only_their_own_attempts_newest_first(self):
        self.submit(self.student, code='print(1)')
        self.submit(self.student, code='print(2)')
        self.submit(self.classmate, code='secret()')

        self.client.force_login(self.student)
        attempts = self.client.get(self.url()).json()

        self.assertEqual([a['code'] for a in attempts], ['print(2)', 'print(1)'])

    def test_instructor_cannot_list_through_student_endpoint(self):
        self.client.force_login(self.teacher)

        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_course_assignment_list_shows_own_attempt_count(self):
        self.submit(self.student)
        self.submit(self.student)
        self.submit(self.classmate)
        self.client.force_login(self.student)

        [assignment] = self.client.get(f'/courses/{self.course.id}/assignments').json()

        self.assertEqual(assignment['attempt_count'], 2)

    def test_instructor_list_has_no_attempt_count(self):
        self.client.force_login(self.teacher)

        [assignment] = self.client.get(f'/courses/{self.course.id}/assignments').json()

        self.assertIsNone(assignment['attempt_count'])


class DailyProgressTests(SubmissionTestCase):
    def progress(self, user=None):
        self.client.force_login(user or self.student)
        response = self.client.get('/progress')
        self.assertEqual(response.status_code, 200)
        return response.json()

    def attempt_at(self, when, assignment=None, student=None):
        submission = Submission.objects.create(
            assignment=assignment or self.assignment,
            student=student or self.student,
            attempt_number=Submission.objects.count() + 1,
        )
        # submitted_at is auto_now_add, so it is moved after creation.
        Submission.objects.filter(id=submission.id).update(submitted_at=when)

    def test_new_student_has_no_streak_and_open_tasks(self):
        body = self.progress()

        self.assertEqual(body['streak_days'], 0)
        self.assertFalse(body['practiced_today'])
        self.assertEqual(len(body['week']), 7)
        self.assertEqual([t['title'] for t in body['tasks']], ['Hello world'])
        self.assertEqual((body['completed_tasks'], body['total_tasks']), (0, 1))

    def test_submitting_marks_the_task_done_and_today_practiced(self):
        self.submit(self.student)

        body = self.progress()

        self.assertTrue(body['practiced_today'])
        self.assertEqual(body['streak_days'], 1)
        self.assertTrue(body['tasks'][0]['is_done'])
        self.assertEqual(body['week'][-1]['submissions'], 1)
        self.assertEqual(body['completed_tasks'], 1)

    def test_tasks_include_only_published_work_in_own_courses(self):
        self.make('Draft', status=Assignment.Status.DRAFT)
        self.make('Closed', status=Assignment.Status.CLOSED)
        self.make('Elsewhere', course=self.other_course)

        titles = [t['title'] for t in self.progress()['tasks']]

        self.assertEqual(titles, ['Hello world'])

    def test_tasks_are_sorted_by_deadline_and_flag_overdue(self):
        self.make('Due soon', due_in_days=1)
        overdue = self.make('Overdue', due_in_days=1)
        Assignment.objects.filter(id=overdue.id).update(due_at=timezone.now() - timedelta(hours=1))

        tasks = self.progress()['tasks']

        self.assertEqual([t['title'] for t in tasks], ['Overdue', 'Due soon', 'Hello world'])
        self.assertTrue(tasks[0]['is_overdue'])
        self.assertFalse(tasks[1]['is_overdue'])

    def test_streak_counts_consecutive_days_up_to_yesterday(self):
        now = timezone.now()
        for days_ago in (1, 2, 3, 5):
            self.attempt_at(now - timedelta(days=days_ago))

        body = self.progress()

        # Today is not done yet, but the 3-day streak is still alive.
        self.assertEqual(body['streak_days'], 3)
        self.assertFalse(body['practiced_today'])

    def test_classmates_attempts_do_not_count(self):
        self.submit(self.classmate)

        body = self.progress()

        self.assertEqual(body['streak_days'], 0)
        self.assertFalse(body['tasks'][0]['is_done'])

    def test_day_starts_at_midnight_in_almaty_not_utc(self):
        # 23:30 in Almaty is 18:30 UTC the same day; 00:30 the next day in
        # Almaty is still the previous day in UTC.
        late_evening = datetime(2026, 11, 16, 23, 30, tzinfo=ALMATY)
        just_after_midnight = datetime(2026, 11, 17, 0, 30, tzinfo=ALMATY)
        self.attempt_at(late_evening)
        self.attempt_at(just_after_midnight)

        with mock.patch('django.utils.timezone.now', return_value=datetime(2026, 11, 17, 12, tzinfo=ALMATY)):
            body = self.progress()

        self.assertEqual(body['today'], '2026-11-17')
        self.assertTrue(body['practiced_today'])
        self.assertEqual(body['streak_days'], 2)
        self.assertEqual([d['submissions'] for d in body['week'][-2:]], [1, 1])


class StreakTests(TestCase):
    def test_streak_rules(self):
        today = datetime(2026, 11, 17).date()
        day = lambda n: today - timedelta(days=n)  # noqa: E731

        self.assertEqual(_streak(set(), today), 0)
        self.assertEqual(_streak({day(0)}, today), 1)
        self.assertEqual(_streak({day(0), day(1), day(2)}, today), 3)
        self.assertEqual(_streak({day(1), day(2)}, today), 2)  # alive until tonight
        self.assertEqual(_streak({day(2), day(3)}, today), 0)  # a missed day ends it
