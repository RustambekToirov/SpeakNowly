from enum import Enum


class Constants:
    class PassageLevel(str, Enum):
        EASY = "easy"
        MEDIUM = "medium"
        HARD = "hard"

        @classmethod
        def choices(cls):
            return [(cls.EASY, "Easy"), (cls.MEDIUM, "Medium"), (cls.HARD, "Hard")]

    class QuestionType(str, Enum):
        TEXT = "TEXT"
        MULTIPLE_CHOICE = "MULTIPLE_CHOICE"

        @classmethod
        def choices(cls):
            return [(cls.TEXT, "Text"), (cls.MULTIPLE_CHOICE, "Multiple Choice")]

    class ReadingStatus(str, Enum):
        CANCELLED = "cancelled"
        PENDING = "pending"
        STARTED = "started"
        COMPLETED = "completed"
        EXPIRED = "expired"

        @classmethod
        def choices(cls):
            return [
                (cls.CANCELLED, "Cancelled"),
                (cls.PENDING, "Pending"),
                (cls.STARTED, "Started"),
                (cls.COMPLETED, "Completed"),
                (cls.EXPIRED, "Expired"),
            ]