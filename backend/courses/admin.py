from django.contrib import admin

from .models import Assignment, Course, CourseSection, Enrollment, RubricCriterion, Skill, TestCase


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'term', 'created_at')
    search_fields = ('code', 'title')


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'course')
    list_filter = ('course',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'section', 'role', 'joined_at')
    list_filter = ('course', 'role')
    search_fields = ('user__email', 'user__full_name')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')
    list_filter = ('course',)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'status', 'feedback_depth', 'due_at')
    list_filter = ('course', 'status')


@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    list_display = ('title', 'assignment', 'skill', 'max_points', 'position')
    list_filter = ('assignment',)


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'assignment', 'criterion', 'visibility', 'weight', 'time_limit_ms')
    list_filter = ('assignment', 'visibility')
