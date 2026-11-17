from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import get_my_courses
from .serializers import MyCourseSerializer


class MyCoursesView(APIView):
    """The courses the signed-in user teaches or studies. There is no user id
    in the URL, so nobody can list another user's courses."""

    def get(self, request):
        return Response(MyCourseSerializer(get_my_courses(request.user), many=True).data)
