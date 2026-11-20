"""Suggested points per rubric criterion, from test results alone.

A criterion earns its points in proportion to the weight of its tests that
passed. A criterion with no tests gets no suggestion (None): the instructor
decides it, and later an AI suggestion may fill it in. Tests linked to no
criterion do not count toward points.
"""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal('0.01')


def suggest_points(criteria, results):
    """Returns {criterion_id: Decimal or None} for every criterion.

    `results` are the attempt's TestResult rows with their test_case loaded.
    An attempt whose tests did not run has no results, so its tested criteria
    get 0: nothing was shown to work.
    """
    by_criterion = {}
    for result in results:
        criterion_id = result.test_case.criterion_id
        if criterion_id is not None:
            by_criterion.setdefault(criterion_id, []).append(result)

    tested = {test.criterion_id for criterion in criteria for test in criterion.test_cases.all()}
    suggestions = {}
    for criterion in criteria:
        if criterion.id not in tested:
            suggestions[criterion.id] = None
            continue
        weights = {test.id: test.weight for test in criterion.test_cases.all()}
        total = sum(weights.values(), Decimal(0))
        passed_results = [result for result in by_criterion.get(criterion.id, []) if result.passed]
        passed = sum((weights.get(result.test_case_id, Decimal(0)) for result in passed_results), Decimal(0))
        suggestions[criterion.id] = (criterion.max_points * passed / total).quantize(CENT, ROUND_HALF_UP)
    return suggestions

