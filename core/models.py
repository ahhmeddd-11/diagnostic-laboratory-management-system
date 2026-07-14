from django.db import models
from accounts.models import User

class ActivityLog(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_column='user_id')
    user_name = models.CharField(max_length=100, null=True, blank=True)
    action_type = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ActivityLogs'
