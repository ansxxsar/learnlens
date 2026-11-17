from django.urls import path

from .views import MyCoursesView

urlpatterns = [
    path('', MyCoursesView.as_view(), name='my-courses'),
]
