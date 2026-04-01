#!/usr/bin/env python3
"""
HACKATHON SUBMISSION FINAL VERIFICATION

Maps to HACKATHON_CHECKLIST.md requirements.
Run this before submitting to ensure zero disqualification risk.
"""

import subprocess
import requests
import json
from pathlib import Path
from typing import Tuple

BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).parent


class HackathonVerifier:
    """Verify all hackathon submission requirements."""
    
    def __init__(self):
        self.checks = {
            "disqualification": [],
            "golden_ratio": [],
            "baseline": [],
            "defensive": [],
            "wow_factor": [],
        }
        self.passed = 0
        self.failed = 0
    
    def test(self, category: str, description: str, condition: bool, details: str = ""):
        """Record a test result."""
        symbol = "✅" if condition else "❌"
        print(f"  {symbol} {description}")
        if details and not condition:
            print(f"     → {details}")
        
        self.checks[category].append((description, condition))
        
        if condition:
            self.passed += 1
        else:
            self.failed += 1
        
        return condition
    
    def print_category(self, title: str):
        """Print category header."""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}\n")
    
    # ========================================================================
    # SECTION 1: DISQUALIFICATION ZERO-TOLERANCE CHECK
    # ========================================================================
    
    def verify_disqualification_checks(self):
        """Section 1: Disqualification Zero-Tolerance Check"""
        self.print_category("1️⃣  DISQUALIFICATION ZERO-TOLERANCE CHECK")
        
        # Check 1: openenv.yaml exists and is valid
        openenv_path = PROJECT_ROOT / "openenv.yaml"
        self.test("disqualification", 
                 "openenv.yaml exists at root",
                 openenv_path.exists(),
                 f"File not found: {openenv_path}")
        
        if openenv_path.exists():
            try:
                import yaml
                with open(openenv_path) as f:
                    config = yaml.safe_load(f)
                    has_required = all(k in config for k in ['api', 'environment', 'network', 'tasks'])
                    self.test("disqualification",
                             "openenv.yaml has all required sections",
                             has_required)
            except Exception as e:
                self.test("disqualification",
                         "openenv.yaml is valid YAML",
                         False,
                         str(e))
        
        # Check 2: Dockerfile exists
        dockerfile_path = PROJECT_ROOT / "Dockerfile"
        self.test("disqualification",
                 "Dockerfile exists at root",
                 dockerfile_path.exists() and dockerfile_path.is_file(),
                 "Must be a file, not directory")
        
        # Check 3: API responding
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=2)
            self.test("disqualification",
                     "API health check (HTTP 200)",
                     resp.status_code == 200)
        except Exception as e:
            self.test("disqualification",
                     "API health check (HTTP 200)",
                     False,
                     "Is the container running? docker run -p 8000:8000 ...")
        
        # Check 4: reset() returns valid JSON
        try:
            resp = requests.post(f"{BASE_URL}/reset", json={})
            data = resp.json()
            valid = "state" in data
            self.test("disqualification",
                     "reset() returns valid JSON observation",
                     valid,
                     f"Response: {data}")
        except Exception as e:
            self.test("disqualification",
                     "reset() returns valid JSON observation",
                     False,
                     str(e))
        
        # Check 5: Domain validation (not a classic game)
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            with open(readme_path) as f:
                content = f.read().lower()
                is_game = any(word in content for word in 
                            ["chess", "tic-tac-toe", "snake", "pong", "tetris"])
                self.test("disqualification",
                         "Target domain is NOT a classic game",
                         not is_game,
                         "Avoid: Chess, Tic-Tac-Toe, Snake, etc.")
    
    # ========================================================================
    # SECTION 2: THE GOLDEN RATIO (3 TASKS)
    # ========================================================================
    
    def verify_golden_ratio(self):
        """Section 2: The Golden Ratio (3 Tasks)"""
        self.print_category("2️⃣  THE GOLDEN RATIO (3 TASKS)")
        
        # Check 1: Get tasks
        try:
            resp = requests.get(f"{BASE_URL}/tasks")
            data = resp.json()
            tasks = data.get("data", {}).get("tasks", [])
            
            self.test("golden_ratio",
                     "GET /tasks endpoint exists (HTTP 200)",
                     resp.status_code == 200)
            
            self.test("golden_ratio",
                     "Exactly 3 tasks defined",
                     len(tasks) == 3,
                     f"Found {len(tasks)} tasks")
            
            # Check distinct properties
            if len(tasks) >= 3:
                schemas = [t.get("action_schema", {}) for t in tasks]
                props_sets = [set(s.get("properties", {}).keys()) for s in schemas]
                
                # At least Task 3 should be different
                all_different = not (props_sets[0] == props_sets[1] == props_sets[2])
                self.test("golden_ratio",
                         "Action schemas have DISTINCT properties",
                         all_different,
                         "Task 3 must have unique fields (cargo_type, split_at)")
                
                # Check Task 3 specifics
                task3 = next((t for t in tasks if "multimodal" in t.get("id", "")), None)
                if task3:
                    props = task3.get("action_schema", {}).get("properties", {})
                    has_cargo_type = "cargo_type" in props
                    has_split_at = "split_at" in props
                    
                    self.test("golden_ratio",
                             "Task 3 has cargo_type field",
                             has_cargo_type)
                    
                    self.test("golden_ratio",
                             "Task 3 has split_at field",
                             has_split_at)
        
        except Exception as e:
            self.test("golden_ratio",
                     "Tasks endpoint",
                     False,
                     str(e))
        
        # Check 2: Grader endpoint
        try:
            resp = requests.post(
                f"{BASE_URL}/grader",
                json={"trajectory": []}
            )
            data = resp.json()
            
            self.test("golden_ratio",
                     "POST /grader endpoint exists (HTTP 200)",
                     resp.status_code == 200)
            
            score = data.get("data", {}).get("score")
            self.test("golden_ratio",
                     "Grader returns score in [0.0, 1.0]",
                     score is not None and 0.0 <= score <= 1.0,
                     f"Score: {score}")
        
        except Exception as e:
            self.test("golden_ratio",
                     "Grader endpoint",
                     False,
                     str(e))
    
    # ========================================================================
    # SECTION 3: BASELINE SCRIPT PROOF
    # ========================================================================
    
    def verify_baseline_script(self):
        """Section 3: Baseline Script Proof"""
        self.print_category("3️⃣  BASELINE SCRIPT PROOF")
        
        baseline_path = PROJECT_ROOT / "baseline" / "run_baseline.py"
        
        self.test("baseline",
                 "baseline/run_baseline.py exists",
                 baseline_path.exists())
        
        if baseline_path.exists():
            with open(baseline_path) as f:
                content = f.read()
                
                self.test("baseline",
                         "Accepts --base-url argument",
                         "--base-url" in content)
                
                self.test("baseline",
                         "Has exception handling (try/except)",
                         "try:" in content and "except" in content)
                
                self.test("baseline",
                         "Calls sys.exit(0) on success",
                         "exit(0)" in content or "sys.exit(0)" in content)
    
    # ========================================================================
    # SECTION 4: DEFENSIVE PROGRAMMING
    # ========================================================================
    
    def verify_defensive_programming(self):
        """Section 4: Defensive Programming Check"""
        self.print_category("4️⃣  DEFENSIVE PROGRAMMING CHECK")
        
        # Check Python files for bare raises and silent fails
        python_files = list((PROJECT_ROOT / "app").glob("**/*.py"))
        
        issues = {"bare_raise": 0, "silent_fail": 0}
        
        for py_file in python_files:
            with open(py_file) as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if "except:" in line and "pass" in lines[i+1] if i+1 < len(lines) else False:
                        issues["silent_fail"] += 1
        
        self.test("defensive",
                 "NO bare `except: pass` (silent failures)",
                 issues["silent_fail"] == 0,
                 f"Found {issues['silent_fail']} silent failures")
        
        # Check core_env for setup
        core_env = PROJECT_ROOT / "app" / "engine" / "core_env.py"
        if core_env.exists():
            with open(core_env) as f:
                content = f.read()
                
                has_max_steps = "max_steps" in content
                self.test("defensive",
                         "Environment has max_steps enforcement",
                         has_max_steps,
                         "Prevents infinite episodes")
                
                has_uuid = "uuid" in content.lower()
                self.test("defensive",
                         "Uses UUID for episode_id",
                         has_uuid)
        
        # Check grader for boundaries
        grader = PROJECT_ROOT / "app" / "api" / "grader.py"
        if grader.exists():
            with open(grader) as f:
                content = f.read()
                
                has_boundaries = "max(0" in content and "min(1" in content
                self.test("defensive",
                         "Score boundaries enforced (0 ≤ score ≤ 1)",
                         has_boundaries,
                         "Use: max(0.0, min(1.0, score))")
    
    # ========================================================================
    # SECTION 5: WOW FACTOR
    # ========================================================================
    
    def verify_wow_factor(self):
        """Section 5: Wow Factor (Human Judging)"""
        self.print_category("5️⃣  WOW FACTOR (HUMAN JUDGING)")
        
        readme = PROJECT_ROOT / "README.md"
        self.test("wow_factor",
                 "README.md exists and documented",
                 readme.exists())
        
        if readme.exists():
            with open(readme) as f:
                content = f.read()
                
                has_action_space = "action" in content.lower()
                has_observation = "observation" in content.lower()
                has_reward = "reward" in content.lower()
                
                documented = has_action_space and has_observation and has_reward
                self.test("wow_factor",
                         "README documents action/observation/reward spaces",
                         documented)
        
        # Check for semantic naming
        grader = PROJECT_ROOT / "app" / "api" / "grader.py"
        if grader.exists():
            with open(grader) as f:
                content = f.read()
                
                has_semantic = all(x in content for x in 
                                 ["accumulated_hours", "accumulated_cost", "accumulated_carbon"])
                self.test("wow_factor",
                         "Uses semantic variable names (not x1, y2, z3)",
                         has_semantic)
        
        # Check git cleanliness
        gitignore = PROJECT_ROOT / ".gitignore"
        self.test("wow_factor",
                 ".gitignore configured (no API keys, logs)",
                 gitignore.exists())
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    def print_summary(self):
        """Print final summary."""
        total = self.passed + self.failed
        
        print(f"\n{'='*80}")
        print(f"HACKATHON SUBMISSION VERIFICATION SUMMARY")
        print(f"{'='*80}\n")
        
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total:  {total}\n")
        
        if self.failed == 0:
            print("🎉 ALL CHECKS PASSED - SUBMISSION READY! 🎉")
            return True
        else:
            print("⚠️  SOME CHECKS FAILED - FIX ISSUES BEFORE SUBMITTING")
            return False
    
    def run_all(self):
        """Run all verification checks."""
        self.verify_disqualification_checks()
        self.verify_golden_ratio()
        self.verify_baseline_script()
        self.verify_defensive_programming()
        self.verify_wow_factor()
        
        return self.print_summary()


if __name__ == "__main__":
    import sys
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*19 + "HACKATHON SUBMISSION FINAL VERIFICATION" + " "*21 + "║")
    print("║" + " "*21 + "Mapping to HACKATHON_CHECKLIST.md" + " "*25 + "║")
    print("╚" + "="*78 + "╝\n")
    
    verifier = HackathonVerifier()
    success = verifier.run_all()
    
    sys.exit(0 if success else 1)
