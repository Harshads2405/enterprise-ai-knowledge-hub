from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class DocumentUnit:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)