from django.urls import path

from .views import StudentCourseAssignmentListView, StudentCourseListView

app_name = "courses"

urlpatterns = [
    path("", StudentCourseListView.as_view(), name="student-course-list"),
    path(
        "<int:course_id>/assignments/",
        StudentCourseAssignmentListView.as_view(),
        name="student-course-assignment-list",
    ),
]