from decimal import Decimal

from rest_framework import serializers

from feedback.serializers import FeedbackSerializer
from submissions.languages import LANGUAGE_BY_FILE

from .scoring import suggest_points

POINTS = {'max_digits': 6, 'decimal_places': 2, 'coerce_to_string': False}


def _summary(submission):
    if submission is None:
        return None
    results = submission.test_results.all()
    return {
        'id': submission.id,
        'attempt_number': submission.attempt_number,
        'status': submission.status,
        'submitted_at': submission.submitted_at,
        'passed_count': sum(result.passed for result in results),
        'test_count': len(results),
    }


def _points(value):
    return None if value is None else float(value)


def gradebook_data(book):
    cells = []
    for (assignment_id, student_id), cell in book.cells.items():
        grade = None
        if cell.graded is not None:
            grade = {
                'submission_id': cell.graded.id,
                'points': _points(sum((s.final_points for s in cell.graded.criterion_scores.all()), Decimal(0))),
                # A newer attempt arrived after this one was graded.
                'is_outdated': cell.graded.id != cell.latest.id,
            }
        cells.append(
            {
                'assignment_id': assignment_id,
                'student_id': student_id,
                'latest': _summary(cell.latest),
                'suggested_points': _points(cell.suggested),
                'needs_review': cell.needs_review,
                'grade': grade,
            }
        )
    return {
        'assignments': [
            {
                'id': assignment.id,
                'title': assignment.title,
                'status': assignment.status,
                'due_at': assignment.due_at,
                'max_points': _points(book.max_points[assignment.id]),
            }
            for assignment in book.assignments
        ],
        'students': [
            {
                'id': enrollment.user_id,
                'full_name': enrollment.user.full_name,
                'section_code': enrollment.section.code if enrollment.section_id else None,
            }
            for enrollment in book.students
        ],
        'cells': cells,
    }


class ReviewResultSerializer(serializers.Serializer):
    """Every test result, hidden ones included. Instructors only."""

    test_name = serializers.CharField(source='test_case.name')
    visibility = serializers.CharField(source='test_case.visibility')
    passed = serializers.BooleanField()
    error_type = serializers.CharField(allow_null=True)
    runtime_ms = serializers.IntegerField(allow_null=True)
    stdin_input = serializers.CharField(source='test_case.stdin_input')
    expected_output = serializers.CharField(source='test_case.expected_output')
    actual_output = serializers.CharField(allow_null=True)
    error_output = serializers.CharField(allow_null=True)


def review_data(submission, other_attempts):
    entry = next((file for file in submission.files.all() if file.is_entry_point), None)
    criteria = list(submission.assignment.rubric_criteria.all())
    results = sorted(submission.test_results.all(), key=lambda result: result.test_case_id)
    suggestions = suggest_points(criteria, results)
    scores = {score.criterion_id: score for score in submission.criterion_scores.all()}
    feedback = getattr(submission, 'feedback', None)

    return {
        **_summary(submission),
        'student': {'id': submission.student_id, 'full_name': submission.student.full_name},
        'assignment': {'id': submission.assignment_id, 'title': submission.assignment.title},
        'language': LANGUAGE_BY_FILE.get(entry.path) if entry else None,
        'code': entry.content if entry else '',
        'results': ReviewResultSerializer(results, many=True).data,
        'feedback': FeedbackSerializer(feedback).data if feedback else None,
        'is_graded': bool(scores),
        'criteria': [
            {
                'id': criterion.id,
                'title': criterion.title,
                'description': criterion.description,
                'max_points': _points(criterion.max_points),
                'is_tested': suggestions[criterion.id] is not None,
                'suggested_points': _points(suggestions[criterion.id]),
                'final_points': _points(scores[criterion.id].final_points) if criterion.id in scores else None,
                'override_reason': scores[criterion.id].override_reason if criterion.id in scores else None,
            }
            for criterion in criteria
        ],
        'attempts': [_summary(attempt) for attempt in other_attempts],
    }


class ScoreInputSerializer(serializers.Serializer):
    criterion = serializers.IntegerField()
    points = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True, required=False)
    reason = serializers.CharField(max_length=2000, allow_blank=True, required=False)


class ApproveGradeSerializer(serializers.Serializer):
    scores = ScoreInputSerializer(many=True, required=False)

    def to_scores(self):
        return {
            item['criterion']: {'points': item.get('points'), 'reason': item.get('reason', '')}
            for item in self.validated_data.get('scores', [])
        }
