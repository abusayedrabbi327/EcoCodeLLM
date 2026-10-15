"""
code_candidate.py — Data class representing a single code solution.

Each candidate tracks its source code, origin, test results, profiling
metrics, and final TOPSIS score through the pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from ecocode.models.profile_result import ProfileResult


@dataclass
class CodeCandidate:
    """
    Represents a single code solution flowing through the EcoCode pipeline.

    Attributes:
        id: Unique identifier (e.g., 'candidate_001').
        source_code: The raw Python source code string.
        origin: Where this code came from — 'llm_generated', 'user_provided',
                or 'ast_rewritten'.
        is_valid: Whether the code passed all unit tests.
        test_results: Test execution details {passed, failed, errors}.
        profile: Profiling metrics (None until profiled).
        topsis_score: Final weighted score (None until scored).
        detected_patterns: Anti-patterns found during Mode 2 analysis.
    """
    id: str
    source_code: str
    origin: str = "llm_generated"
    is_valid: bool = False
    test_results: Dict[str, Any] = field(default_factory=lambda: {
        "passed": 0,
        "failed": 0,
        "errors": [],
    })
    profile: Optional[ProfileResult] = None
    topsis_score: Optional[float] = None
    detected_patterns: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary for JSON export."""
        return {
            "id": self.id,
            "source_code": self.source_code,
            "origin": self.origin,
            "is_valid": self.is_valid,
            "test_results": self.test_results,
            "profile": self.profile.to_dict() if self.profile else None,
            "topsis_score": round(self.topsis_score, 6) if self.topsis_score is not None else None,
            "detected_patterns": self.detected_patterns,
        }

    def __repr__(self) -> str:
        score_str = f"{self.topsis_score:.4f}" if self.topsis_score is not None else "N/A"
        return (
            f"CodeCandidate(id='{self.id}', origin='{self.origin}', "
            f"valid={self.is_valid}, score={score_str})"
        )
