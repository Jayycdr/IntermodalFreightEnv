# Comprehensive Code Analysis Report
## IntermodalFreightEnv Project

**Analysis Date:** April 4, 2026  
**Scope:** Python files in `app/`, `baseline/`, `tests/`, and `scripts/` directories  
**Total Files Analyzed:** 25 Python files  
**Rating Scale:** High Impact | Medium Impact | Low Impact

---

## Executive Summary

The codebase demonstrates solid foundational architecture with a clear FastAPI-based system design. However, there are significant opportunities for improvement in code organization, reduction of technical debt, and enhancement of maintainability. Most critical issues are in code duplication and lack of helper functions for repeated patterns.

**Priority Issues:**
- **HIGH:** Significant code duplication in agent classes and test files
- **HIGH:** Magic numbers and hardcoded configuration values throughout
- **MEDIUM:** Inconsistent error handling patterns
- **MEDIUM:** Missing type hints in several critical classes

---

## 1. CODE STRUCTURE & ORGANIZATION

### Current State
The project is well-organized at the top level with clear separation of concerns:
- `app/` - Core application (API, engine, utilities)
- `baseline/` - Baseline agent implementations
- `tests/` - Test suites
- `scripts/` - Utility scripts

### Issues Found

| File | Location | Issue | Impact | Details |
|------|----------|-------|--------|---------|
| `app/main.py` | Lines 40-75 | Default network hardcoded in function | **HIGH** | Network configuration should be externalized |
| `app/api/grader.py` | Lines 41-66 | Global `MODE_CHARACTERISTICS` dict lacks structure | **MEDIUM** | Consider creating a `TransportationModeCatalog` class |
| `app/engine/core_env.py` | Lines 1-50 | Placeholder implementations in methods | **MEDIUM** | `_update_state()` and `_calculate_reward()` are empty |
| `tests/` directory | - | Test files import same modules differently | **MEDIUM** | Inconsistent import patterns across test suite |

### Recommendations
1. Extract default network config to `config/default_network.json` or similar
2. Create a `TransportationModeCatalog` class to manage mode characteristics
3. Implement complete core_env.py placeholder methods or mark as abstract
4. Standardize test imports with a shared base test configuration

---

## 2. CODE DUPLICATION & COMPLEXITY

### Critical Duplication Areas

#### Duplication Area 1: Agent Base Logic
**Files:** `baseline/agent.py` (lines 27-134)  
**Impact Score:** **HIGH**

Three agent classes (`RandomAgent`, `GreedyAgent`, `DijkstraAgent`) repeat:
1. `_get_available_edges()` extraction logic (16 lines, Lines 84-99)
2. `_get_edge_weight()` weight calculation logic (13 lines, Lines 101-113)
3. Action response formatting (8 lines, repeated in each agent)
4. Task type mapping (5 lines, repeated in `GreedyAgent` and `DijkstraAgent`)

**Example of Duplication:**
```python
# In GreedyAgent (line 203-209)
task_map = {
    "time": "task_1_time",
    "cost": "task_2_cost",
    "carbon": "task_3_multimodal",
}
action = { "task_type": task_map.get(...), "cargo_id": 0, "path": path }

# In DijkstraAgent (line 267-273)
task_map = {
    "time": "task_1_time",
    "cost": "task_2_cost",
    "carbon": "task_3_multimodal",
}
action = { "task_type": task_map.get(...), "cargo_id": 0, "path": path }
```

**Refactoring Opportunity:**
Extract to base class method: `BaseAgent._build_action(self, weight_type: str, cargo_id: int, path: List[int])`

---

#### Duplication Area 2: Test Setup Code
**Files:** `tests/test_api_layer.py`, `tests/test_core_systems.py`, `tests/test_environment_logic.py`  
**Impact Score:** **HIGH**

Network configuration is duplicated across three test files:
- `test_api_layer.py` (Lines 30-50): Network setup
- `test_core_systems.py` (Lines 45-65): Similar network setup
- `test_environment_logic.py`: References same structure

Each has similar node/edge definitions with slight variations.

**Refactoring Opportunity:**
- Create `tests/fixtures.py` with `create_test_network()` factory function
- Use in all test files: `from tests.fixtures import create_test_network`

---

#### Duplication Area 3: Metric Accumulation Logic
**Files:** `app/api/grader.py` (lines 231-248), `tests/test_mathematics.py` (lines 54-69)  
**Impact Score:** **MEDIUM**

Metric score calculation is implemented in:
1. `Grader._calculate_weighted_score()` (4 lines)
2. Test validation (4 lines)
3. Script calculations (multiple files)

**Example:**
```python
# In grader.py line 237
score = (
    0.5 * metrics.accumulated_hours +
    0.3 * metrics.accumulated_cost +
    0.2 * metrics.accumulated_carbon
)

# In test_mathematics.py line 66
expected_score = 0.5 * 7.5 + 0.3 * 123.45 + 0.2 * 67.89
```

**Refactoring Opportunity:**
Create constants module: `app/constants.py`
```python
TRILEMMA_WEIGHTS = {
    "hours": 0.5,
    "cost": 0.3,
    "carbon": 0.2,
}
```

---

#### Duplication Area 4: Response Creation Patterns
**Files:** `baseline/run_baseline.py`, `app/main.py`, `scripts/*.py`  
**Impact Score:** **MEDIUM**

Pattern repeated:
```python
return BaseResponse(
    success=True,
    message="...",
    data={...}
)
```

Appears in 8+ locations with slight variations.

---

### Summary of Duplications
| Duplication Type | Locations | Lines Affected | Severity |
|-----------------|-----------|----------------|----------|
| Agent action building | 2 places | ~15 lines | HIGH |
| Test network setup | 3 places | ~45 lines | HIGH |
| Metric calculations | 5+ places | ~25 lines | MEDIUM |
| Response formatting | 8+ places | ~40 lines | MEDIUM |
| Graph initialization | 3 places | ~30 lines | MEDIUM |

---

## 3. FUNCTION/METHOD ORGANIZATION & NAMING

### Naming Issues

#### Issue 1: Inconsistent Naming Conventions
**Files:** `app/main.py`, `app/engine/graph.py`  
**Impact Score:** **MEDIUM**

| Location | Current Name | Issue | Suggestion |
|----------|-------------|-------|-----------|
| `core_env.py` L23 | `setup_network()` | Verb form OK but vague | `initialize_network()` (more explicit) |
| `core_env.py` L50 | `_initialize_state()` | Good, private method | ✓ No change |
| `graph.py` L60 | `get_shortest_path()` | Good but ambiguous with multiple weights | Could be `find_shortest_path()` |
| `grader.py` L231 | `_extract_metrics()` | Good private method | ✓ No change |
| `agent.py` L84 | `_get_available_edges()` | Good but could be `_filter_available_edges()` | Minor improvement |

#### Issue 2: Method Length & Single Responsibility
**File:** `app/api/grader.py` - Method `evaluate()`  
**Lines:** 188-244  
**Impact Score:** **MEDIUM**

The `evaluate()` method does too much:
1. Validates trajectory (line 192-195)
2. Extracts metrics (line 198)
3. Calculates weighted score (line 201)
4. Calculates task score (line 204)
5. Counts deliveries (line 207)
6. Calculates efficiency (line 210-213)
7. Generates feedback (line 216-220)
8. Creates result object (line 222-231)

**Recommendation:** This 56-line method should be split. Current helper methods are good, but the orchestration is too complex.

#### Issue 3: Unclear Method Names
**File:** `baseline/agent.py`  
**Impact Score:** **MEDIUM**

| Method | Issue |
|--------|-------|
| `_get_edge_weight()` | What if weight type is invalid? Name doesn't convey default fallback behavior |
| `_build_available_graph()` | Could be `_create_adjacency_list_from_edges()` for clarity |
| `select_action()` | Should clarify it's selecting *one* action per state |

---

## 4. TYPE HINTS USAGE

### Type Hints Coverage

#### Excellent Coverage (90-100%):
- `app/api/schemas.py` - All Pydantic models fully typed
- `app/api/grader.py` - All public methods typed (except one)
- `app/engine/graph.py` - All methods fully typed

#### Good Coverage (70-89%):
- `app/main.py` - Most endpoints typed, some internals missing
- `baseline/agent.py` - All public methods typed

#### Partial Coverage (40-69%):
- `tests/test_api_layer.py` - Function params lack types
- `tests/test_mathematics.py` - Class methods lack return types
- `scripts/debug_agent_learning.py` - Minimal type hints

#### Poor Coverage (<40%):
- `app/engine/core_env.py` - Critical methods lack proper return types
- `tests/test_environment_logic.py` - `test()` method has no type hints (Line 24)

### Specific Issues

| File | Line | Issue | Type |
|------|------|-------|------|
| `core_env.py` | 58 | `_update_state()` returns `Dict[str, Any]` - too vague | Missing Union types |
| `core_env.py` | 62 | `_calculate_reward()` returns `float` - OK but no error handling type | Missing Optional |
| `agent.py` | 84 | `_get_available_edges()` - OK but edge data types are `Dict[str, Any]` | Should use TypedDict |
| `test_api_layer.py` | 13 | `test()` function - no type annotation for `condition`, `expected`, `actual` | Missing types |
| `test_environment_logic.py` | 24 | `test()` method - no return type | Missing return type |

### Recommendations
1. Add `TypedDict` for edge data structure:
   ```python
   # In app/engine/graph.py
   class EdgeAttributes(TypedDict):
       time: float
       cost: float
       carbon: float
       disabled: bool
   ```

2. Use `Union` or `Optional` more explicitly:
   ```python
   # Instead of: Dict[str, Any] 
   # Use: Dict[str, Union[float, int, str]]
   ```

3. Add type hints to all test utility methods

---

## 5. ERROR HANDLING PATTERNS

### Error Handling Assessment

#### Issue 1: Inconsistent Exception Handling
**File:** `baseline/agent.py`  
**Impact Score:** **MEDIUM**

```python
# Line 77-81: Generic exception handler loses context
def _get_state_from_api(self) -> Dict[str, Any]:
    try:
        response = requests.get(f"{self.api_url}/state")
        response.raise_for_status()
        return response.json()
    except Exception as e:  # ← TOO BROAD
        logger.error(f"Failed to fetch state from API: {e}")
        return {}
```

**Should be:**
```python
except requests.RequestException as e:
    logger.error(f"Failed to fetch state from API: {e}")
    return {}
```

#### Issue 2: Silent Failures
**File:** `baseline/run_baseline.py` - Lines 110-125  
**Impact Score:** **HIGH**

```python
response = requests.post(f"{self.api_url}/reset")
response.raise_for_status()  # Can throw, but...
state = response.json()     # ← If JSON parse fails, exception not caught

# Later (lines 130-145):
if response.ok:
    result = response.json()  # ← Inconsistent error handling
    # ...
else:
    reward = 0.0
    done = False
    info = {}
```

**Issues:**
1. Inconsistent error handling patterns
2. Some places use `response.ok`, others use `response.raise_for_status()`
3. JSON parsing not protected by try-except in all places

#### Issue 3: Missing Error Context
**File:** `app/main.py` - Lines 294-307  
**Impact Score:** **MEDIUM**

```python
try:
    env = get_env()
    # ... 20+ lines of code ...
except Exception as e:  # ← Generic catch
    logger.error(f"Failed to add cargo: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
```

**Should distinguish between:**
- `ValueError` - validation errors (400)
- `KeyError` - not found errors (404)
- `RuntimeError` - internal errors (500)

#### Issue 4: No Timeout Handling
**File:** `baseline/agent.py`  
**Impact Score:** **MEDIUM**

```python
response = requests.get(f"{self.api_url}/state")  # ← No timeout specified
```

Should be:
```python
response = requests.get(f"{self.api_url}/state", timeout=5.0)
```

### Error Handling Issues Summary
| Location | Issue | Type | Priority |
|----------|-------|------|----------|
| `agent.py:77` | Generic exception catching | BROAD_EXCEPT | HIGH |
| `run_baseline.py:110` | Inconsistent error handling | INCONSISTENCY | HIGH |
| `main.py:294` | Generic exception in endpoint | MISSING_CONTEXT | MEDIUM |
| `agent.py:75` | No HTTP timeout | MISSING_CONFIG | MEDIUM |
| `grader.py:380` | Silent failure in unknown weight type | SILENT_FAIL | MEDIUM |
| `test_environment_logic.py:58` | No error handling in test assertions | TEST_FRAGILITY | LOW |

### Recommendations
1. Create exception hierarchy in `app/exceptions.py`:
   ```python
   class FreightEnvironmentError(Exception): pass
   class CargoError(FreightEnvironmentError): pass
   class NetworkError(FreightEnvironmentError): pass
   class ValidationError(FreightEnvironmentError): pass
   ```

2. Use specific exception catching throughout

3. Add timeout configurations to all requests

---

## 6. DOCUMENTATION & DOCSTRINGS

### Documentation Coverage

#### Excellent Documentation:
- `app/api/schemas.py` - All Pydantic models have Field descriptions and examples
- `app/api/grader.py` - All public methods have detailed docstrings with formula documentation
- `app/engine/graph.py` - All methods well-documented with Args/Returns
- `app/main.py` - All endpoints have docstrings explaining their purpose

#### Good Documentation:
- `baseline/agent.py` - All agent classes documented, but could explain algorithm details
- `tests/test_core_systems.py` - Test functions have explanatory comments

#### Poor Documentation:
- `app/engine/core_env.py` - Critical methods have minimal documentation (lines 46-62)
- `tests/test_mathematics.py` - Test classes lack high-level description
- `scripts/debug_agent_learning.py` - Classes have no module-level docstrings
- `tests/test_api_layer.py` - Missing explanation of what "structural distinctness" means

### Specific Documentation Issues

| File | Location | Issue | Type |
|------|----------|-------|------|
| `core_env.py` | L46-62 | `_update_state()` and `_calculate_reward()` have no docstrings | MISSING |
| `core_env.py` | L1-10 | Module docstring doesn't explain placeholder status | UNCLEAR |
| `test_api_layer.py` | L150+ | Comments about "STRUCTURALLY DISTINCT" not clear to new readers | VAGUE |
| `baseline/agent.py` | L159-169 | Comments about Dijkstra but algorithm explanation missing | INCOMPLETE |

### Missing Module-Level Documentation

Files missing module-level docstrings explaining their purpose:
- `app/utils/__init__.py`
- `app/api/__init__.py`
- `tests/__init__.py`

---

## 7. IMPORT ORGANIZATION

### Import Organization Status

#### Good (Well-organized):
- `app/api/schemas.py` - Grouped by: stdlib, third-party, local (Lines 8-12)
- `tests/test_mathematics.py` - Clear grouping with blank lines (Lines 7-18)

#### Issues Found

| File | Location | Issue | Severity |
|------|----------|-------|----------|
| `app/main.py` | Lines 1-22 | Mixed import order (stdlib, third-party, local not separated) | MEDIUM |
| `baseline/agent.py` | Lines 7-12 | `requests` imported before `abc`, not alphabetical | LOW |
| `tests/test_core_systems.py` | Lines 1-8 | Inconsistent import style vs other test files | LOW |
| `scripts/run_all_math_tests.py` | Lines 9-10 | Relative imports mixed with absolute | MEDIUM |

### Import Issues Detail

#### Issue 1: Circular Import Risk
**File:** `app/main.py` - Lines 12-18  
**Potential Problem:**
```python
from app.engine.core_env import FreightEnvironment, EnvironmentConfig
from app.api.grader import TrilemmaMetrics  # ← Uses TaskType, conflicts with schemas
```

Both `grader.py` and `schemas.py` define `TaskType` enum - **potential for confusion**

#### Issue 2: Unused Imports
**File:** `baseline/run_baseline.py` - Line 10  
**Issue:** `Dict, List, Any, Optional` imported but some not used

#### Issue 3: Import Organization Not Following PEP 8
**File:** `app/main.py` - Lines 1-22

```python
# Current:
from typing import Optional
import requests
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Should be (PEP 8):
import requests
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.utils.logger import logger
```

### Import Organization Improvements

| Issue | Files | Recommendation | Priority |
|-------|-------|-----------------|----------|
| Duplicate TaskType enum | `grader.py`, `schemas.py` | Move to single location | HIGH |
| Inconsistent grouping | 4+ files | Enforce import ordering (isort) | MEDIUM |
| Unused imports | 2+ files | Clean up | LOW |
| Mixed relative/absolute | 2 files | Use absolute imports consistently | MEDIUM |

### Recommendations
1. Use `isort` tool to enforce consistent import ordering
2. Consolidate `TaskType` enum to single location (`app/enums.py` or `app/constants.py`)
3. Create configuration in `pyproject.toml` or `.isort.cfg`:
   ```ini
   [tool.isort]
   profile = "black"
   multi_line_mode = 3
   include_trailing_comma = true
   ```

---

## 8. CLASS DESIGN & RESPONSIBILITIES

### Class Design Analysis

#### Issue 1: Single Responsibility Principle Violation
**File:** `app/api/grader.py`  
**Class:** `Grader`  
**Impact Score:** **MEDIUM**

The `Grader` class has too many responsibilities:
1. Trajectory loading and storage (lines 172-187)
2. Metrics extraction (lines 248-273)
3. Score calculation (lines 275-295)
4. Efficiency scoring (lines 335-360)
5. Feedback generation (lines 362-389)
6. Trajectory comparison (lines 456-475)

**Recommendation:** Extract into separate classes:
```python
class TrajectoryAnalyzer:
    """Load and extract metrics from trajectories"""
    
class ScoringEngine:
    """Calculate weighted scores and efficiency"""
    
class FeedbackGenerator:
    """Generate human-readable feedback"""
    
class GraderOrchestrator:
    """Uses above classes to grade trajectories"""
```

---

#### Issue 2: God Object - FreightEnvironment
**File:** `app/engine/core_env.py`  
**Class:** `FreightEnvironment`  
**Impact Score:** **MEDIUM**

Currently manages:
- Environment state (lines 30-33)
- Network configuration (lines 35-36)
- Step simulation (lines 46-62)
- Reward calculation (placeholder)

Should be split:
```python
# Separate into:
class EnvironmentState:
    """Manages environment state only"""
    
class NetworkManager:
    """Manages network structure"""
    
class SimulationEngine:
    """Manages state transitions and rewards"""
```

---

#### Issue 3: Base Class Incomplete
**File:** `baseline/agent.py`  
**Class:** `BaseAgent`  
**Impact Score:** **MEDIUM**

The `BaseAgent` class defines API interaction but doesn't enforce critical methods:
```python
class BaseAgent(ABC):
    @abstractmethod
    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
```

**Issues:**
1. No abstract methods for action formatting (subclasses repeat the same mapping)
2. `_get_available_edges()` should be abstract but isn't
3. No method to validate actions before returning

**Recommendation:**
```python
@abstractmethod
def validate_action(self, action: Dict[str, Any]) -> bool:
    """Validate action before execution"""
    pass

def _format_action(self, weight_type: str, cargo_id: int, path: List[int]) -> Dict[str, Any]:
    """Common action formatting - extracted from subclasses"""
```

---

#### Issue 4: Method Cohesion in Test Classes
**File:** `tests/test_environment_logic.py`  
**Class:** `EnvironmentTester`  
**Impact Score:** **LOW**

Class mixes:
1. Test execution logic (test())
2. Test result recording (self.test_results)
3. Format-specific output (print_summary())

Should be split into:
```python
class TestRecorder:
    """Records test results"""
    
class TestOutput:
    """Formats and prints results"""
```

---

### Class Design Issues Summary
| Class | File | Issue | Severity | Lines |
|-------|------|-------|----------|-------|
| Grader | grader.py | Too many responsibilities | HIGH | 56+ |
| FreightEnvironment | core_env.py | Needs fragmentation | MEDIUM | All |
| BaseAgent | agent.py | Incomplete abstraction | MEDIUM | 27-134 |
| EnvironmentTester | test_environment_logic.py | Mixed concerns | LOW | 20-120 |

---

## 9. MAGIC NUMBERS & HARDCODED VALUES

### Critical Hardcoded Values

#### Hardcoding 1: Default Network in get_env()
**File:** `app/main.py`  
**Lines:** 52-75  
**Impact Score:** **HIGH**

```python
default_network = {
    "nodes": [
        {"id": 0, "location": "Warehouse"},
        # ... 5 more nodes hardcoded ...
    ],
    "edges": [
        {"source": 0, "target": 1, "time": 2.0, "cost": 100.0, "carbon": 30.0},
        # ... 9 more edges hardcoded ...
    ],
}
```

**Issues:**
- Network structure fixed at runtime
- Can't easily test different topologies
- Network changes require code modifications
- No versioning or rollback capability

**Refactoring:**
- Move to `config/default_network.json`
- Load via configuration loader

---

#### Hardcoding 2: Trilemma Weights
**Files:** 5+ locations  
**Impact Score:** **HIGH**

Hard-coded in multiple locations:
- `app/api/grader.py` lines 237-240
- `tests/test_mathematics.py` lines 66, 92, etc.
- `tests/test_regressions.py` lines 32-33
- `scripts/debug_agent_learning.py` (calculation examples)

```python
# In grader.py:
score = (
    0.5 * metrics.accumulated_hours +
    0.3 * metrics.accumulated_cost +
    0.2 * metrics.accumulated_carbon
)
```

**Should be:**
```python
# constants.py
TRILEMMA_WEIGHTS = {
    "hours": 0.5,
    "cost": 0.3,  
    "carbon": 0.2,
}

# grader.py
score = sum(
    weight * getattr(metrics, f"accumulated_{key}")
    for key, weight in TRILEMMA_WEIGHTS.items()
)
```

---

#### Hardcoding 3: Numeric Thresholds
**File:** `app/api/grader.py` - Efficiency calculation  
**Lines:** 352-356  
**Impact Score:** **MEDIUM**

```python
# Base score calculation
metric_score = max(0, 100 - (weighted_score / 10))  # ← Why divide by 10?

# Bonus calculations
delivery_bonus = deliveries * 10  # ← Why 10?

# Step penalty
step_penalty = max(0, (num_steps - 10) * 0.5)  # ← Why 10? Why 0.5?
```

**Refactoring:**
```python
# constants.py
EFFICIENCY_CALCULATION = {
    "metric_score_scale": 10,      # Divide by this
    "delivery_bonus_per_unit": 10,
    "step_threshold": 10,
    "step_penalty_rate": 0.5,
}
```

---

#### Hardcoding 4: HTTP Endpoints
**Files:** `baseline/agent.py`, `baseline/run_baseline.py`, test files  
**Lines:** Multiple  
**Impact Score:** **MEDIUM**

```python
BASE_URL = "http://localhost:8000"  # ← In 5 different files

# In agent.py, line 31:
def __init__(self, agent_id: str, api_url: str = "http://localhost:8000"):
```

Should be:
```python
# config.py
DEFAULT_API_URL = "http://localhost:8000"

# Or from environment:
import os
DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000")
```

---

#### Hardcoding 5: Test Configuration Magic Numbers
**File:** `tests/test_core_systems.py`  
**Lines:** 40-45  
**Impact Score:** **MEDIUM**

```python
config = EnvironmentConfig(
    num_nodes=6,
    max_steps=10,
    disruption_probability=0.1,  # ← Where do these numbers come from?
    seed=42,
)
```

**Recommendation:** Create test fixtures/constants:
```python
# tests/constants.py
SMALL_NETWORK_CONFIG = EnvironmentConfig(
    num_nodes=6,
    max_steps=10,
    disruption_probability=0.1,
    seed=42,
)
```

---

### Magic Numbers Summary
| Category | Locations | Count | Priority |
|----------|-----------|-------|----------|
| Trilemma weights | 5+ | 0.5, 0.3, 0.2 | HIGH |
| Default network | 1 | 10 nodes + edges | HIGH |
| Efficiency thresholds | grader.py | 10, 10, 0.5 | HIGH |
| HTTP endpoints | 5+ | localhost:8000 | MEDIUM |
| Test values | 3 | 6 nodes, 10 steps, 0.1 prob | MEDIUM |
| Score normalization | 2 | 100, 50 | LOW |

---

## 10. OPPORTUNITIES FOR HELPER FUNCTIONS

### Helper Function Opportunities

#### Opportunity 1: Network Setup Helper
**Impact Score:** **HIGH**  
**Duplication:** 3+ locations

**Current Problem:**
```python
# In test_core_systems.py, test_api_layer.py, etc.
network_config = {
    "nodes": [...],
    "edges": [...]
}
env.setup_network(network_config)
```

**Create Helper:**
```python
# app/network_helpers.py
def create_network_config(
    nodes: List[Tuple[int, str, Optional[float]]] = None,
    edges: List[Tuple[int, int, float, float, float]] = None
) -> Dict[str, Any]:
    """Create network configuration from node/edge definitions.
    
    Args:
        nodes: List of (id, location_name, capacity)
        edges: List of (source, target, time, cost, carbon)
        
    Returns:
        Network config dict
    """
    if nodes is None:
        nodes = DEFAULT_NODES
    if edges is None:
        edges = DEFAULT_EDGES
        
    return {
        "nodes": [{"id": n[0], "location": n[1], **} for n in nodes],
        "edges": [{"source": e[0], "target": e[1], "time": e[2], ...} for e in edges],
    }
```

---

#### Opportunity 2: Agent Action Builder
**Impact Score:** **HIGH**  
**Duplication:** Repeated in `RandomAgent`, `GreedyAgent`, `DijkstraAgent`

**Current Problem:**
```python
# In each agent class:
action = {
    "task_type": task_map.get(self.weight_type, "task_1_time"),
    "cargo_id": 0,
    "path": path,
}
```

**Create Helper in BaseAgent:**
```python
class BaseAgent(ABC):
    WEIGHT_TO_TASK_MAP = {
        "time": "task_1_time",
        "cost": "task_2_cost",
        "carbon": "task_3_multimodal",
    }
    
    def _build_action(
        self,
        weight_type: str,
        cargo_id: int,
        path: List[int]
    ) -> Dict[str, Any]:
        """Build standardized action dict."""
        return {
            "task_type": self.WEIGHT_TO_TASK_MAP.get(weight_type, "task_1_time"),
            "cargo_id": cargo_id,
            "path": path,
        }
    
    # In subclasses:
    def select_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        path = ...  # Algorithm-specific
        return self._build_action(self.weight_type, 0, path)
```

---

#### Opportunity 3: HTTP Request Error Handling
**Impact Score:** **MEDIUM**  
**Duplication:** 10+ locations with requests

**Current Problem:**
```python
# In multiple places:
try:
    response = requests.get(f"{self.api_url}/state")
    response.raise_for_status()
    return response.json()
except Exception as e:
    logger.error(f"Failed: {e}")
    return {}
```

**Create Helper:**
```python
# app/http_helpers.py
def safe_request(
    method: str,
    url: str,
    default_response: Any = None,
    **kwargs
) -> Any:
    """Safely make HTTP request with error handling.
    
    Args:
        method: HTTP method (get, post, etc.)
        url: Request URL
        default_response: Return if request fails
        **kwargs: Passed to requests
        
    Returns:
        Response JSON or default_response
    """
    try:
        if method.lower() == "get":
            response = requests.get(url, timeout=5.0, **kwargs)
        elif method.lower() == "post":
            response = requests.post(url, timeout=5.0, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        return default_response or {}
```

---

#### Opportunity 4: Metric Validation
**Impact Score:** **MEDIUM**  
**Duplication:** Similar validation in `Grader.evaluate()` and tests

**Create Helper:**
```python
# app/validation_helpers.py
def validate_metrics(metrics: TrilemmaMetrics) -> bool:
    """Validate metrics are non-negative."""
    return all([
        metrics.accumulated_hours >= 0,
        metrics.accumulated_cost >= 0,
        metrics.accumulated_carbon >= 0,
    ])

def normalize_metrics(
    metrics: TrilemmaMetrics,
    max_hours: float = 100,
    max_cost: float = 10000,
    max_carbon: float = 1000,
) -> Tuple[float, float, float]:
    """Normalize metrics to 0-1 range."""
    return (
        min(metrics.accumulated_hours / max_hours, 1.0),
        min(metrics.accumulated_cost / max_cost, 1.0),
        min(metrics.accumulated_carbon / max_carbon, 1.0),
    )
```

---

#### Opportunity 5: Response Building Helper
**Impact Score:** **MEDIUM**  
**Duplication:** 15+ BaseResponse creations

**Create Helper:**
```python
# app/response_helpers.py
def success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
) -> BaseResponse:
    """Build success response."""
    return BaseResponse(success=True, message=message, data=data)

def error_response(
    message: str,
    detail: Optional[str] = None,
) -> BaseResponse:
    """Build error response."""
    return BaseResponse(
        success=False,
        message=message,
        data={"error": detail} if detail else None
    )
```

---

#### Opportunity 6: Configuration Loading
**Impact Score:** **MEDIUM**  
**Current Issue:** Hardcoded defaults everywhere

**Create Helper:**
```python
# app/config_loader.py
import json
from pathlib import Path
from typing import Dict, Any

def load_network_config(config_path: str = "config/default_network.json") -> Dict[str, Any]:
    """Load network config from JSON file."""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file {config_path} not found, using defaults")
        return DEFAULT_NETWORK
    
    with open(path) as f:
        return json.load(f)

def load_env_config() -> EnvironmentConfig:
    """Load environment config from environment variables or file."""
    return EnvironmentConfig(
        num_nodes=int(os.getenv("NUM_NODES", 10)),
        max_steps=int(os.getenv("MAX_STEPS", 1000)),
        seed=int(os.getenv("SEED", 42)) if os.getenv("SEED") else None,
    )
```

---

### Helper Functions Recommendations Summary

| Helper Function | Files Affected | Duplication Reduced | Priority |
|-----------------|-----------------|-------------------|----------|
| `create_network_config()` | 3+ test files | 45+ lines | HIGH |
| `BaseAgent._build_action()` | 3 agent classes | 20+ lines | HIGH |
| `safe_request()` | 10+ locations | 30+ lines | HIGH |
| `success_response()` | 15+ endpoints | 30+ lines | MEDIUM |
| `validate_metrics()` | grader, tests | 10+ lines | MEDIUM |
| `load_network_config()` | main.py + tests | 20+ lines | MEDIUM |

---

## PRIORITIZED ACTION ITEMS

### Critical (Should Fix Immediately - HIGH PRIORITY)

| ID | Issue | Location | Impact | Effort | Estimated Gain |
|---|-------|----------|--------|--------|-----------------|
| 1 | Extract hardcoded network to config file | `app/main.py` L52-75 | Testability, maintainability | Medium | 30 lines reduced |
| 2 | Create `_build_action()` helper in BaseAgent | `baseline/agent.py` | Code duplication | Low | 15 lines reduced |
| 3 | Move trilemma weights to constants | `app/api/grader.py` + 4 files | Magic numbers | Low | 5+ locations simplified |
| 4 | Consolidate TaskType enum | Multiple | Consistency | Low | Prevent bugs |
| 5 | Add specific exception catching | `baseline/agent.py` | Error handling | Low | Better debugging |

### High Value (Should Plan in Next Sprint - MEDIUM PRIORITY)

| ID | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 6 | Extract test network to `fixtures.py` | Tests (3 files) | Code duplication | Medium |
| 7 | Add missing type hints | `core_env.py`, tests | Type safety | Medium |
| 8 | Create helper response builders | `app/main.py` + endpoints | Code duplication | Low |
| 9 | Split Grader class into 3 classes | `app/api/grader.py` | Single responsibility | High |
| 10 | Create HTTP request wrapper | Multiple | Error handling, consistency | Medium |

### Nice-to-Have (Long-term Improvements - LOW PRIORITY)

| ID | Issue | Location | Impact | Effort |
|---|-------|----------|--------|--------|
| 11 | Use isort for import organization | All files | Code style | Low |
| 12 | Add module-level docstrings | Multiple | Documentation | Low |
| 13 | Extract configuration to environment variables | Multiple | DevOps | Medium |
| 14 | Create custom exception hierarchy | Multiple | Error handling | Medium |
| 15 | Implement comprehensive logging strategy | Multiple | Debugging | Medium |

---

## SUMMARY BY CATEGORY

| Category | Status | Issues | Priority |
|----------|--------|--------|----------|
| Code Structure | Good | 4 issues | MEDIUM |
| Duplication | **Poor** | 4 major areas | **HIGH** |
| Naming | Good | 3 minor issues | MEDIUM |
| Type Hints | Good | 5 critical gaps | MEDIUM |
| Error Handling | Fair | 6 issues | HIGH |
| Documentation | Good | 4 areas | MEDIUM |
| Imports | Fair | 4 issues | MEDIUM |
| Class Design | Fair | 4 violations | MEDIUM |
| Magic Numbers | **Poor** | 5+ categories | **HIGH** |
| Helper Functions | **Poor** | 6 opportunities | **HIGH** |

---

## RECOMMENDED REFACTORING SEQUENCE

### Phase 1: Foundation (Week 1)
1. Create `app/constants.py` with trilemma weights and thresholds
2. Move network to `config/default_network.json`
3. Create exception hierarchy in `app/exceptions.py`

### Phase 2: Duplication Reduction (Week 2)
1. Extract test network to `tests/fixtures.py`
2. Add `_build_action()` to `BaseAgent`
3. Extract response builders to helper module

### Phase 3: Code Quality (Week 3)
1. Add missing type hints to critical files
2. Implement `safe_request()` wrapper
3. Split `Grader` class

### Phase 4: Polish (Week 4)
1. Add module-level docstrings
2. Implement isort configuration
3. Update error handling to use custom exceptions

---

## CONCLUSION

The codebase has a solid foundation with good API design and test coverage. The main opportunities for improvement are:

1. **Reducing code duplication** through helper functions and shared utilities (HIGH impact)
2. **Eliminating magic numbers** into constants and configuration (HIGH impact)  
3. **Improving error handling** with specific exceptions and consistent patterns (MEDIUM impact)
4. **Adding type hints** to critical paths (MEDIUM impact)
5. **Refactoring large classes** to follow single responsibility principle (MEDIUM impact)

Implementing the Phase 1 recommendations would immediately improve maintainability and reduce technical debt. Estimated total effort: **40-60 hours** for all recommended improvements.

---

**Report Generated:** April 4, 2026
**Analyzed Files:** 25 Python files
**Total Findings:** 42 issues across 10 categories
