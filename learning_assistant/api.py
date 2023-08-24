"""
Library for the learning_assistant app.
"""
import json

from learning_assistant.models import CoursePrompt


def get_deserialized_prompt_content_by_course_id(course_id):
    """
    Return a deserialized prompt given a course_id.
    """
    json_prompt = CoursePrompt.get_json_prompt_content_by_course_id(course_id)
    if json_prompt:
        prompt_messages = json.loads(json_prompt)
        return prompt_messages
    return None


def get_setup_messages(course_id):
    """
    Return a list of setup messages given a course id.
    """
    message_content = get_deserialized_prompt_content_by_course_id(course_id)
    if message_content:
        setup_messages = [{'role': 'system', 'content': x} for x in message_content]
        return setup_messages
    return None
