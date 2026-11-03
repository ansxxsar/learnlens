"""Phase 2 (course setup) tables from docs/erd/learnlens-erd.drawio.

Table and column names match the ERD exactly. Django adds "_id" to a
ForeignKey name, so `course = ForeignKey(...)` becomes the column course_id.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Course(models.Model):
    """ERD table "courses"."""

    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    term = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses'

    def __str__(self):
        return f'{self.code} – {self.title}'


class CourseSection(models.Model):
    """ERD table "course_sections": a group of students inside one course."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    code = models.CharField(max_length=50)

    class Meta:
        db_table = 'course_sections'
        constraints = [
            # Two sections of the same course cannot share a code.
            models.UniqueConstraint(fields=['course', 'code'], name='unique_section_code_per_course'),
        ]

    def __str__(self):
        return f'{self.course.code} / {self.code}'


class Enrollment(models.Model):
    """ERD table "enrollments": links a user to a course with a role."""

    class Role(models.TextChoices):
        STUDENT = 'student'
        INSTRUCTOR = 'instructor'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    # Optional: instructors may teach the whole course without a section.
    section = models.ForeignKey(
        CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments'
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'enrollments'
        constraints = [
            # A user can be enrolled in a course only once.
            models.UniqueConstraint(fields=['user', 'course'], name='unique_enrollment_per_course'),
        ]

    def __str__(self):
        return f'{self.user} in {self.course.code} ({self.role})'

    def clean(self):
        # The section must belong to the same course as the enrollment.
        # A plain database constraint cannot compare columns across two
        # tables, so this rule is checked here in Python.
        if self.section_id and self.course_id and self.section.course_id != self.course_id:
            raise ValidationError({'section': 'This section belongs to a different course.'})

    def save(self, *args, **kwargs):
        # Run the check on every save, not only in admin forms.
        self.clean()
        super().save(*args, **kwargs)


class Skill(models.Model):
    """ERD table "skills": a learning skill tracked within a course."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'skills'

    def __str__(self):
        return self.name


class Assignment(models.Model):
    """ERD table "assignments"."""

    class Status(models.TextChoices):
        DRAFT = 'draft'
        PUBLISHED = 'published'
        CLOSED = 'closed'
        ARCHIVED = 'archived'

    class FeedbackDepth(models.TextChoices):
        HINT = 'hint'
        GUIDED = 'guided'
        DETAILED = 'detailed'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    instructions = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    feedback_depth = models.CharField(max_length=20, choices=FeedbackDepth.choices, default=FeedbackDepth.GUIDED)
    due_at = models.DateTimeField()
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assignments'

    def __str__(self):
        return self.title


class RubricCriterion(models.Model):
    """ERD table "rubric_criteria": one scored item of an assignment's rubric."""

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='rubric_criteria')
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='rubric_criteria')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    max_points = models.DecimalField(max_digits=6, decimal_places=2)
    position = models.IntegerField(default=0)  # display order within the rubric

    class Meta:
        db_table = 'rubric_criteria'
        ordering = ['position']
        verbose_name_plural = 'rubric criteria'

    def __str__(self):
        return self.title


class TestCase(models.Model):
    """ERD table "test_cases": an input/expected-output check for an assignment.

    Hidden test cases must never be shown to students (see AGENTS.md).
    """

    class Visibility(models.TextChoices):
        PUBLIC = 'public'
        HIDDEN = 'hidden'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='test_cases')
    criterion = models.ForeignKey(
        RubricCriterion, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_cases'
    )
    name = models.CharField(max_length=255)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.HIDDEN)
    stdin_input = models.TextField(blank=True)
    expected_output = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    time_limit_ms = models.IntegerField(default=2000)

    class Meta:
        db_table = 'test_cases'

    def __str__(self):
        return self.name
