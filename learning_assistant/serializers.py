"""
Serializers for the learning-assistant API.
"""
from rest_framework import serializers


class MessageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for a message.
    """

    role = serializers.CharField(required=True)
    content = serializers.CharField(required=True)

    def validate_role(self, value):
        """
        Validate that role is one of two acceptable values.
        """
        valid_roles = ['user', 'assistant']
        if value not in valid_roles:
            raise serializers.ValidationError('Must be valid role.')
        return value
