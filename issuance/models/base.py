from django.conf import settings
from django.db import models

from issuance.middleware import get_current_user


class UserTrackingModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        db_index=True
    )
    created_by_role = models.CharField(max_length=50, blank=True, null=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        db_index=True
    )
    updated_by_role = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def _safe_get_role(self, user):
        if not user:
            return None

        get_role = getattr(user, "get_role_display", None)
        if callable(get_role):
            try:
                return get_role()
            except Exception:
                pass

        for attr in ("role", "role_name"):
            if hasattr(user, attr):
                try:
                    return str(getattr(user, attr))
                except Exception:
                    pass
        return None

    def save(self, *args, **kwargs):
        user = get_current_user()

        if user and not self.pk:
            self.created_by = user
            role = self._safe_get_role(user)
            if role:
                self.created_by_role = role

        if user:
            self.updated_by = user
            role = self._safe_get_role(user)
            if role:
                self.updated_by_role = role

        super().save(*args, **kwargs)
