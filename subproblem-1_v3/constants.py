

from enum import Enum


class UserRole(str, Enum):

    ENGINEERING = "ENGINEERING"

    MARKETING = "MARKETING"

    FINANCE = "FINANCE"

    HR = "HR"

    IT = "IT"

    LEGAL = "LEGAL"

    EXECUTIVE = "EXECUTIVE"


ROLE_DISTRIBUTION = {

    UserRole.ENGINEERING: 0.40,

    UserRole.MARKETING: 0.15,

    UserRole.FINANCE: 0.15,

    UserRole.HR: 0.10,

    UserRole.IT: 0.10,

    UserRole.LEGAL: 0.05,

    UserRole.EXECUTIVE: 0.05

}


ROLE_RESOURCES = {

    UserRole.ENGINEERING: [

        "/api/v1/engineering/wiki",

        "/api/v1/engineering/build",

        "/api/v1/engineering/github"

    ],

    UserRole.MARKETING: [

        "/api/v1/marketing/campaigns",

        "/api/v1/marketing/budget",

        "/api/v1/marketing/assets"

    ],

    UserRole.FINANCE: [

        "/api/v1/finance/payroll",

        "/api/v1/finance/invoices",

        "/api/v1/finance/reports"

    ],

    UserRole.HR: [

        "/api/v1/hr/employees",

        "/api/v1/hr/recruitment",

        "/api/v1/hr/leave"

    ],

    UserRole.IT: [

        "/api/v1/it/monitoring",

        "/api/v1/it/assets",

        "/api/v1/it/helpdesk"

    ],

    UserRole.LEGAL: [

        "/api/v1/legal/contracts",

        "/api/v1/legal/compliance"

    ],

    UserRole.EXECUTIVE: [

        "/api/v1/executive/dashboard",

        "/api/v1/executive/reports"

    ]

}


WORLD_LOCATIONS = [

    ("Mumbai", "India", 19.0760, 72.8777),

    ("Delhi", "India", 28.6139, 77.2090),

    ("Berlin", "Germany", 52.5200, 13.4050),

    ("London", "United Kingdom", 51.5074, -0.1278),

    ("New York", "USA", 40.7128, -74.0060),

    ("Sydney", "Australia", -33.8688, 151.2093),

    ("Tokyo", "Japan", 35.6895, 139.6917)

]


OPERATING_SYSTEMS = [

    "Windows 11",

    "Ubuntu 24.04",

    "macOS 15",

    "Windows 10"

]


BROWSERS = [

    "Chrome/126",

    "Firefox/126",

    "Edge/126",

    "Safari/17"

]