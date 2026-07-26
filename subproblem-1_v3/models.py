

from dataclasses import dataclass
from dataclasses import field

from datetime import datetime

from typing import List
from typing import Tuple
from typing import Optional


@dataclass(slots=True)
class UserProfile:

    entity_id: str

    role: str

    department: str

    primary_ip: str

    home_geo: Tuple[float, float]

    primary_device_id: str

    primary_os: str

    user_agent: str

    habitual_start_hour: int

    habitual_end_hour: int

    allowed_resources: List[str]

    manager: str

    country: str

    city: str

    timezone: str

    risk_score: float


@dataclass(slots=True)
class UserSession:

    entity_id: str
    employee_name: str = ""
    email: str = ""
    office_location: str = ""

    state: str = "OFFLINE"

    session_id: Optional[str] = None

    is_logged_in: bool = False

    current_ip: Optional[str] = None

    current_device: Optional[str] = None

    failed_login_attempts: int = 0

    last_login: Optional[datetime] = None

    last_activity: Optional[datetime] = None

    idle_minutes: int = 0

    resources_accessed: List[str] = field(default_factory=list)