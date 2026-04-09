"""
Application-wide constants and magic numbers.

Consolidates all hardcoded values to enable easy maintenance and configuration.
"""

# ============================================================================
# Trilemma Weights for Scoring Formula
# ============================================================================
# Score = TRILEMMA_WEIGHT_TIME × time + TRILEMMA_WEIGHT_COST × cost + TRILEMMA_WEIGHT_CARBON × carbon

TRILEMMA_WEIGHT_TIME = 0.5       # Weight for time/hours metric
TRILEMMA_WEIGHT_COST = 0.3       # Weight for cost metric
TRILEMMA_WEIGHT_CARBON = 0.2     # Weight for carbon/emissions metric

# Verify weights sum to 1.0 (sanity check)
TRILEMMA_WEIGHTS_SUM = (
    TRILEMMA_WEIGHT_TIME + TRILEMMA_WEIGHT_COST + TRILEMMA_WEIGHT_CARBON
)
assert abs(TRILEMMA_WEIGHTS_SUM - 1.0) < 1e-10, \
    f"Trilemma weights must sum to 1.0, got {TRILEMMA_WEIGHTS_SUM}"


# ============================================================================
# Efficiency Score Calculation Factors
# ============================================================================

EFFICIENCY_SCORE_METRIC_DIVISOR = 10.0      # Divide weighted score by this to get metric score
EFFICIENCY_DELIVERY_BONUS = 10.0            # Points per successful delivery
EFFICIENCY_STEP_THRESHOLD = 10              # Steps below this have no penalty
EFFICIENCY_STEP_PENALTY_PER_STEP = 0.5      # Penalty per step over threshold
EFFICIENCY_SCORE_MAX = 99.9                 # Maximum efficiency score (maps to 0.999 after /100)
EFFICIENCY_SCORE_MIN = 0.1                  # Minimum efficiency score (maps to 0.001 after /100)


# ============================================================================
# Efficiency Score Thresholds (for feedback)

EFFICIENCY_EXCELLENT_THRESHOLD = 80.0      # Score >= 80 is excellent
EFFICIENCY_GOOD_THRESHOLD = 60.0           # Score >= 60 is good
EFFICIENCY_FAIR_THRESHOLD = 40.0           # Score >= 40 is fair
EFFICIENCY_POOR_THRESHOLD = 0.0            # Score < 0 is poor


# ============================================================================
# Environment Configuration
# ============================================================================

DEFAULT_MAX_STEPS = 1000                   # Maximum simulation steps per episode
DEFAULT_INITIAL_DEMAND = 100               # Initial cargo demand
DEFAULT_DISRUPTION_PROBABILITY = 0.1       # Probability of network disruption
DEFAULT_NETWORK_NODES = 6                  # Standard network size
DEFAULT_NETWORK_CAPACITY = 1000.0          # Default node capacity


# ============================================================================
# API Configuration
# ============================================================================

API_HOST = "0.0.0.0"
API_PORT = 7860                            # Port for Hugging Face Spaces
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"
API_WORKERS = 1
API_LOG_LEVEL = "info"


# ============================================================================
# HTTP Request Configuration
# ============================================================================

DEFAULT_REQUEST_TIMEOUT = 5.0              # Timeout in seconds for HTTP requests
DEFAULT_RETRY_COUNT = 3                    # Number of retries for failed requests
DEFAULT_RETRY_DELAY = 1.0                  # Delay between retries in seconds


# ============================================================================
# Agent Configuration
# ============================================================================

BASELINE_AGENT_EPISODE_STEPS = 100         # Steps per baseline episode
BASELINE_AGENT_RANDOM_SEED = 42            # Random seed for reproducibility
AGENT_ACTION_TIMEOUT = 5.0                 # Timeout for agent action selection


# ============================================================================
# Task-Specific Configuration
# ============================================================================

TASK_1_OBJECTIVE = "minimize-time"
TASK_2_OBJECTIVE = "minimize-cost"
TASK_3_OBJECTIVE = "balance-trilemma"

TASK_TIMEOUT_SECONDS = 300                # Timeout for task execution


# ============================================================================
# Default Network Topology (6 nodes)
# ============================================================================

DEFAULT_NETWORK_NODES_CONFIG = [
    {"id": 0, "location": "Warehouse", "capacity": 1000.0},
    {"id": 1, "location": "Port A", "capacity": 500.0},
    {"id": 2, "location": "Rail Hub", "capacity": 800.0},
    {"id": 3, "location": "Air Terminal", "capacity": 200.0},
    {"id": 4, "location": "Truck Terminal", "capacity": 600.0},
    {"id": 5, "location": "Destination", "capacity": 400.0},
]


# ============================================================================
# Transportation Mode Characteristics
# ============================================================================

TRUCK_SPEED_KMH = 80.0
TRUCK_COST_PER_KM = 0.15
TRUCK_CARBON_PER_KM = 0.025
TRUCK_CAPACITY_TONS = 25.0
TRUCK_MIN_DISTANCE = 50.0

RAIL_SPEED_KMH = 90.0
RAIL_COST_PER_KM = 0.08
RAIL_CARBON_PER_KM = 0.008
RAIL_CAPACITY_TONS = 100.0
RAIL_MIN_DISTANCE = 200.0

SHIP_SPEED_KMH = 40.0
SHIP_COST_PER_KM = 0.05
SHIP_CARBON_PER_KM = 0.003
SHIP_CAPACITY_TONS = 500.0
SHIP_MIN_DISTANCE = 500.0

FLIGHT_SPEED_KMH = 900.0
FLIGHT_COST_PER_KM = 1.0
FLIGHT_CARBON_PER_KM = 0.15
FLIGHT_CAPACITY_TONS = 50.0
FLIGHT_MIN_DISTANCE = 300.0


# ============================================================================
# Logging Configuration
# ============================================================================

LOG_FORMAT = "{time} | {level: <8} | {name}:{function}:{line} - {message}"
LOG_LEVEL = "INFO"
LOG_FILE = "logs/app.log"
