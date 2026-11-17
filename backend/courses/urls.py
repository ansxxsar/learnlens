from django.urls import path

from submissions.views import MyAttemptsView

from .views import AssignmentDetailView, CourseAssignmentsView, CourseDetailView

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
]
