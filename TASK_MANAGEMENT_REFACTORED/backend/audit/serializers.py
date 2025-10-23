from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    institution = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = '__all__'
    
    def get_institution(self, obj):
        if obj.institution:
            return {
                "id": obj.institution.id,
                "name": obj.institution.institution_name
            }
        return None

    def get_user(self, obj):
        if obj.user:
            return {
                "id": obj.user.id,
                "name": obj.user.fullname
            }
        return None