from django.db import models


class BannedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField(blank=True)
    banned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} ({self.reason})"


# Legacy/unused model kept only because its table already exists in
# production (created by the original 0001_initial migration).
class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
    )
    age = models.IntegerField()