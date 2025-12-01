from django.db import models
from django.contrib.auth.models import User

class AdventureSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    book_title = models.CharField(max_length=255)
    chosen_character = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.book_title} - {self.id}"

class Chapter(models.Model):
    session = models.ForeignKey(AdventureSession, on_delete=models.CASCADE, related_name="chapters")
    text = models.TextField()
    options = models.JSONField(default=list)  # list of { "id": 1, "text": "..."}
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
