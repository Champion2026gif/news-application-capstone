from django.db import models


class ApprovedArticleLog(models.Model):
    """
    Logs every POST made to /api/approved/. This is the "external
    sharing" record referred to in the brief - in a real deployment this
    endpoint might forward to a partner API; here it persists the event
    so it can be inspected/tested.
    """
    article_id = models.IntegerField()
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=150)
    publisher = models.CharField(max_length=255, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ApprovedArticleLog(article_id={self.article_id}, title={self.title!r})"
