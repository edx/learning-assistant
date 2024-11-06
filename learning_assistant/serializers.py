"""
Serializers for the learning-assistant API.
"""
from rest_framework import serializers

from learning_assistant.models import LearningAssistantMessage


class MessageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for a message.
    """

    role = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    timestamp = serializers.DateTimeField(required=False, source='created')

    class Meta:
        """
        Serializer metadata.
        """

        model = LearningAssistantMessage
        fields = (
            'role',
            'content',
            'timestamp',
        )

    def validate_role(self, value):
        """
        Validate that role is one of two acceptable values.
        """
        valid_roles = [LearningAssistantMessage.USER_ROLE, LearningAssistantMessage.ASSISTANT_ROLE]
        if value not in valid_roles:
            raise serializers.ValidationError('Must be valid role.')
        return value
