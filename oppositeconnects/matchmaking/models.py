from django.db import models


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    name   = models.CharField(max_length=100)
    city   = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age    = models.IntegerField()
    # link to Django user if needed
    # user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.name} ({self.gender})"


class BannedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    reason     = models.TextField(blank=True)
    banned_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BANNED: {self.ip_address}"