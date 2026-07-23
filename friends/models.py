from django.db import models
from django.conf import settings
from django.db.models import Q


class FriendRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_friend_requests",
        on_delete=models.CASCADE,
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_friend_requests",
        on_delete=models.CASCADE,
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"], name="unique_friend_request_pair"
            )
        ]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"


class Friendship(models.Model):
    """A confirmed friendship. Always stored with user1.id < user2.id
    so a pair only ever exists once, in either direction."""

    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="friendship_as_user1", on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="friendship_as_user2", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user1", "user2"], name="unique_friendship_pair")
        ]

    def __str__(self):
        return f"{self.user1} <-> {self.user2}"

    @staticmethod
    def create(user_a, user_b):
        u1, u2 = sorted([user_a, user_b], key=lambda u: u.id)
        obj, _ = Friendship.objects.get_or_create(user1=u1, user2=u2)
        return obj

    @staticmethod
    def are_friends(user_a, user_b) -> bool:
        u1, u2 = sorted([user_a, user_b], key=lambda u: u.id)
        return Friendship.objects.filter(user1=u1, user2=u2).exists()

    @staticmethod
    def for_user(user):
        return Friendship.objects.filter(Q(user1=user) | Q(user2=user))

    def other(self, user):
        return self.user2 if self.user1_id == user.id else self.user1


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE
    )
    text = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.text[:30]}"