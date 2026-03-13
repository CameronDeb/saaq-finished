"""
SAAQ Data Models & API Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


# ─── Enums ─────────────────────────────────────────────────────
class IntakeVersion(str, Enum):
    FORUM_15Q = "15Q"
    MASTER_30Q = "30Q"

class ReportStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


# ─── Intake ────────────────────────────────────────────────────
class IntakeSubmission(BaseModel):
    """What the frontend sends when someone completes the survey."""
    first_name: str
    email: Optional[str] = None
    version: IntakeVersion = IntakeVersion.FORUM_15Q
    responses: dict[str, str]  # question_text -> answer_text


class IntakeResponse(BaseModel):
    """What the API returns after submission."""
    id: str
    first_name: str
    version: str
    status: ReportStatus
    created_at: str
    message: str


# ─── Report ────────────────────────────────────────────────────
class ReportRequest(BaseModel):
    """Request to generate a report for a specific intake."""
    intake_id: str

class ReportStatusResponse(BaseModel):
    id: str
    intake_id: str
    subject: str
    status: ReportStatus
    created_at: str
    completed_at: Optional[str] = None
    download_url: Optional[str] = None

class ReportListItem(BaseModel):
    id: str
    subject: str
    email: Optional[str] = None
    version: str
    status: ReportStatus
    created_at: str
    completed_at: Optional[str] = None


# ─── Batch ─────────────────────────────────────────────────────
class BatchRequest(BaseModel):
    """Request to generate reports for multiple intakes."""
    intake_ids: list[str]

class BatchStatusResponse(BaseModel):
    total: int
    completed: int
    failed: int
    pending: int
    reports: list[ReportListItem]


# ─── Admin / Dashboard ────────────────────────────────────────
class DashboardStats(BaseModel):
    total_intakes: int
    total_reports: int
    pending_reports: int
    completed_reports: int


# ─── Questions ─────────────────────────────────────────────────
QUESTIONS_15Q = [
    "Describe a recent challenge. What happened, and how did you deal with it?",
    "When you're overwhelmed or afraid, what happens in your body, and how does it show up in your behavior?",
    "Looking back, how has your understanding of yourself and the world changed most over the years?",
    "Tell us about a time when you felt misunderstood. How did you handle it, and what did you learn?",
    "Tell us about a time when your values were tested. What did you discover about yourself?",
    "Can you describe a moment when you felt pulled between two opposing values, impulses, or desires? How did you navigate that conflict?",
    "What do you notice about your inner voice or self-talk? How do you relate to it?",
    "How do you typically process emotions\u2014your own and others'? Have strong feelings ever clouded your clarity?",
    "In groups, what role do you most often play? How do others tend to experience you?",
    "How do you stay open to people with very different views? What helps you stay connected?",
    "What really gets under your skin about other people? What do you most admire?",
    "How do you relate to your body and energy right now? Has this changed over time?",
    "What is money, and how do you relate to it? What habits, emotions, or stories come up around earning, spending, saving, or investing?",
    "What role do creativity and imagination play in your life? How do you express them?",
    "How do you understand or connect with something larger than yourself (God, spirit, Universe)?",
]

QUESTIONS_30Q = [
    # Core 15
    "Describe a recent challenge. What happened, and how did you deal with it?",
    "When you're overwhelmed or afraid, what happens in your body, and how does it show up in your behavior?",
    "Looking back, how has your understanding of yourself and the world changed most over the years?",
    "Tell us about a time when you felt misunderstood. How did you handle it, and what did you learn?",
    "Tell us about a time when your values were tested. What did you discover about yourself?",
    "Can you describe a moment when you felt pulled between two opposing values, impulses, or desires? How did you navigate that conflict?",
    "What do you notice about your inner voice or self-talk? How do you relate to it?",
    "How do you typically process emotions\u2014your own and others'? Have strong feelings ever clouded your clarity?",
    "In groups, what role do you most often play? How do others tend to experience you?",
    "How do you stay open to people with very different views? What helps you stay connected?",
    "What really gets under your skin about other people? What do you most admire?",
    "Tell us about a relationship that deeply shaped you\u2014for better or worse. How did you respond, and what did you learn?",
    "How do you relate to your body and energy right now? Has this changed over time?",
    "What is money?",
    "How do you relate to money? What habits, emotions, or stories come up around earning, spending, saving, or investing?",
    "What is time?",
    "How do you relate to time? What habits, emotions, or stories come up around your experience of time?",
    "What role do creativity and imagination play in your life? How do you express them?",
    "How do you understand or connect with something larger than yourself (God, spirit, Universe)?",
    "When you've been involved in a group or community, what role did you naturally play?",
    "How do you challenge your own thinking? Tell us about a person, idea, book, insight, or experience that challenged and stretched your perspective.",
    "Tell us about a time when you followed through on something difficult. What drove you?",
    "Tell us about a time when you had to hold back \u2014 when restraint mattered more than action.",
    "Tell us about a time when you could have taken advantage of a situation but chose not to. What guided your choice?",
    "When it comes to tasks and commitments, how do you balance thoroughness with efficiency?",
    "Think of a time when you influenced others without relying on authority. How did you gain their trust or move them toward action?",
    "What gives your life meaning? Has that sense of purpose changed over the years?",
    "When you face setbacks, what does your self-talk sound like?",
    "How do you respond when someone disappoints you or doesn't meet your expectations?",
    "What kinds of new ventures, ideas, art, or experiences most inspire or stretch you?",
]

def get_questions(version: IntakeVersion) -> list[str]:
    return QUESTIONS_30Q if version == IntakeVersion.MASTER_30Q else QUESTIONS_15Q