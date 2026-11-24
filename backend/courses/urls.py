from django.urls import path

from grading.views import ApproveGradeView, AttemptReviewView, GradebookView
from submissions.views import MyAttemptsView

from .views import (
    AssignmentDetailView,
    AssignmentRubricView,
    AssignmentTestsView,
    CourseAssignmentsView,
    CourseDetailView,
    RubricCriterionDetailView,
    TestCaseDetailView,
)

ASSIGNMENT = '<int:course_id>/assignments/<int:assignment_id>'

# Mounted at "courses/". The list itself is "/courses" (no trailing slash, like
# the /auth routes) and is registered in config/urls.py.
urlpatterns = [
    path('<int:course_id>', CourseDetailView.as_view(), name='course-detail'),
    path('<int:course_id>/assignments', CourseAssignmentsView.as_view(), name='course-assignments'),
    path(
        '<int:course_id>/assignments/<int:assignment_id>',
        AssignmentDetailView.as_view(),
        name='assignment-detail',
    ),
    path(
        '<int:course_id>/assignments/<int:assignment_id>/submissions',
        MyAttemptsView.as_view(),
        name='my-attempts',
    ),
    path(f'{ASSIGNMENT}/rubric', AssignmentRubricView.as_view(), name='assignment-rubric'),
    path(f'{ASSIGNMENT}/rubric/<int:criterion_id>', RubricCriterionDetailView.as_view(), name='rubric-criterion'),
    path(f'{ASSIGNMENT}/tests', AssignmentTestsView.as_view(), name='assignment-tests'),
    path(f'{ASSIGNMENT}/tests/<int:test_id>', TestCaseDetailView.as_view(), name='test-case'),
    # Instructors only: the gradebook, one attempt in full, and approving its grade.
    path('<int:course_id>/gradebook', GradebookView.as_view(), name='gradebook'),
    path(f'{ASSIGNMENT}/attempts/<int:submission_id>', AttemptReviewView.as_view(), name='attempt-review'),
    path(f'{ASSIGNMENT}/attempts/<int:submission_id>/grade', ApproveGradeView.as_view(), name='attempt-grade'),
]
