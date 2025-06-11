from django.db import models
from django.contrib.auth.models import User

class FanSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    speed = models.IntegerField(default=155)
    is_on = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Fan Settings"
    

class FanLog(models.Model):  # Add this new model
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # "TURN_ON", "SPEED_CHANGE"
    speed = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
