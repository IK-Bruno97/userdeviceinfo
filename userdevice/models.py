from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class DeviceInfo(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user_info')
    device = models.CharField(max_length=50)
    ip_add = models.CharField(max_length=25)
    date = models.DateTimeField(auto_now=True)

