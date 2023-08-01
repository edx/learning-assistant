"""
Library for the learning_assistant app.
"""
from learning_assistant.models import CoursePrompt


def get_prompt_by_course_id(course_id):
    """
    Return a prompt associated with a given course id.
    """
    return CoursePrompt.get_prompt_by_course_id(course_id)
