from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Assignment, Course, CourseSection, Enrollment


class CourseSetupConstraintTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='student@example.com', full_name='Test Student', password='test-pass-123'
        )
        self.course = Course.objects.create(code='CS101', title='Intro to Programming', term='Fall 2026')

    def test_user_cannot_enroll_twice_in_same_course(self):
        Enrollment.objects.create(user=self.user, course=self.course)

        # The database rejects the duplicate (unique user_id + course_id).
        with self.assertRaises(IntegrityError), transaction.atomic():
            Enrollment.objects.create(user=self.user, course=self.course)

    def test_sections_in_one_course_cannot_share_a_code(self):
        CourseSection.objects.create(course=self.course, code='A')

        with self.assertRaises(IntegrityError), transaction.atomic():
            CourseSection.objects.create(course=self.course, code='A')

    def test_same_section_code_is_allowed_in_different_courses(self):
        other_course = Course.objects.create(code='CS102', title='Data Structures', term='Fall 2026')
        CourseSection.objects.create(course=self.course, code='A')
        CourseSection.objects.create(course=other_course, code='A')  # no error

        self.assertEqual(CourseSection.objects.filter(code='A').count(), 2)

    def test_enrollment_cannot_use_section_from_another_course(self):
        other_course = Course.objects.create(code='CS102', title='Data Structures', term='Fall 2026')
        other_section = CourseSection.objects.create(course=other_course, code='A')

        with self.assertRaises(ValidationError):
            Enrollment.objects.create(user=self.user, course=self.course, section=other_section)
        self.assertFalse(Enrollment.objects.exists())

    def test_enrollment_can_use_section_from_same_course(self):
        section = CourseSection.objects.create(course=self.course, code='A')

        enrollment = Enrollment.objects.create(user=self.user, course=self.course, section=section)

        self.assertEqual(enrollment.section, section)


class StudentCourseApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="student@example.com",
            full_name="Test Student",
            password="test-pass-123",
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@example.com",
            full_name="Other Student",
            password="test-pass-123",
        )

        self.course = Course.objects.create(
            code="CS101",
            title="Intro to Programming",
            term="Fall 2026",
        )
        self.other_course = Course.objects.create(
            code="CS102",
            title="Data Structures",
            term="Fall 2026",
        )

        Enrollment.objects.create(user=self.user, course=self.course)
        Enrollment.objects.create(
            user=self.other_user,
            course=self.other_course,
        )

    def test_course_list_requires_authentication(self):
        response = self.client.get(
            reverse("courses:student-course-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_student_sees_only_their_courses(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            reverse("courses:student-course-list")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "CS101")
        self.assertEqual(response.data[0]["assignment_count"], 0)

    def test_student_sees_only_published_assignments(self):
        published = Assignment.objects.create(
            course=self.course,
            title="Variables",
            instructions="Create and print a variable.",
            status=Assignment.Status.PUBLISHED,
            due_at=timezone.now(),
            published_at=timezone.now(),
        )
        Assignment.objects.create(
            course=self.course,
            title="Draft assignment",
            instructions="Not visible yet.",
            status=Assignment.Status.DRAFT,
            due_at=timezone.now(),
        )

        self.client.force_authenticate(self.user)

        response = self.client.get(
            reverse(
                "courses:student-course-assignment-list",
                kwargs={"course_id": self.course.id},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], published.id)

    def test_student_cannot_read_another_students_course(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(
            reverse(
                "courses:student-course-assignment-list",
                kwargs={"course_id": self.other_course.id},
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
