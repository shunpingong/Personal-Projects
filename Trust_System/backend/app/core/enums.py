from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    moderator = "moderator"
    user = "user"


class ReportStatus(str, Enum):
    pending = "pending"
    reviewed = "reviewed"
    escalated = "escalated"
