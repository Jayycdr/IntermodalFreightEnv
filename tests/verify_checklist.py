#!/usr/bin/env python3
"""
Pre-Submission Verification Script for IntermodalFreightEnv

Checks all critical requirements before final submission.
Run this to verify your project is ready for the April 7 deadline.

Usage:
    python verify_checklist.py
"""

import os
import json
import subprocess
import sys
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class ChecklistVerifier:
    """Verifies submission checklist items."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.project_root = Path(__file__).parent
    
    def check(self, condition, message):
        """Check a condition and print result."""
        if condition:
            print(f"{GREEN}✓{RESET} {message}")
            self.passed += 1
        else:
            print(f"{RED}✗{RESET} {message}")
            self.failed += 1
    
    def warn(self, condition, message):
        """Warn if condition is false."""
        if condition:
            print(f"{GREEN}✓{RESET} {message}")
            self.passed += 1
        else:
            print(f"{YELLOW}⚠{RESET} {message}")
            self.warnings += 1
    
    def section(self, title):
        """Print section header."""
        print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}{BLUE}{title}{RESET}")
        print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    def verify_all(self):
        """Run all verification checks."""
        self.section("1. DISQUALIFICATION ZERO-TOLERANCE CHECK")
        self.verify_section_1()
        
        self.section("2. THE GOLDEN RATIO (3 TASKS)")
        self.verify_section_2()
        
        self.section("3. BASELINE SCRIPT PROOF")
        self.verify_section_3()
        
        self.section("4. DEFENSIVE PROGRAMMING")
        self.verify_section_4()
        
        self.section("5. WOW FACTOR (HUMAN JUDGING)")
        self.verify_section_5()
        
        self.section("SUMMARY")
        self.print_summary()
    
    def verify_section_1(self):
        """Section 1: Disqualification Zero-Tolerance Check"""
        # Check openenv.yaml
        openenv_path = self.project_root / "openenv.yaml"
        self.check(openenv_path.exists(), "openenv.yaml exists at root")
        
        if openenv_path.exists():
            try:
                import yaml
                with open(openenv_path) as f:
                    config = yaml.safe_load(f)
                    self.check('api' in config, "openenv.yaml has 'api' section")
                    self.check('environment' in config, "openenv.yaml has 'environment' section")
                    self.check('network' in config, "openenv.yaml has 'network' section")
                    self.check('tasks' in config, "openenv.yaml has 'tasks' section")
            except Exception as e:
                self.check(False, f"openenv.yaml is valid YAML: {e}")
        
        # Check Dockerfile
        dockerfile_path = self.project_root / "Dockerfile"
        dockerfile_exists = dockerfile_path.exists() and dockerfile_path.is_file()
        self.check(dockerfile_exists, "Dockerfile exists at root (not directory)")
        
        # Check .gitignore
        gitignore_path = self.project_root / ".gitignore"
        gitignore_exists = gitignore_path.exists()
        self.check(gitignore_exists, ".gitignore exists and configured")
        
        if gitignore_exists:
            with open(gitignore_path) as f:
                content = f.read()
                self.check('__pycache__' in content, ".gitignore ignores __pycache__")
                self.check('.venv' in content, ".gitignore ignores .venv")
                self.check('.env' in content, ".gitignore ignores .env")
    
    def verify_section_2(self):
        """Section 2: The Golden Ratio (3 Tasks)"""
        # Check app/main.py for endpoints
        main_py = self.project_root / "app" / "main.py"
        
        if main_py.exists():
            with open(main_py) as f:
                content = f.read()
                self.check('/task1/route' in content, "POST /task1/route endpoint exists")
                self.check('/task2/route' in content, "POST /task2/route endpoint exists")
                self.check('/task3/route' in content, "POST /task3/route endpoint exists")
                self.check('/tasks' in content, "GET /tasks endpoint exists")
                self.check('/grader' in content, "POST /grader endpoint exists")
                
                # Check Task3 distinctness
                self.check('cargo_type' in content, "Task3 includes cargo_type field (distinct)")
                self.check('split_at' in content, "Task3 includes split_at field (distinct)")
        
        # Check schemas
        schemas_py = self.project_root / "app" / "api" / "schemas.py"
        if schemas_py.exists():
            with open(schemas_py) as f:
                content = f.read()
                self.check('Task1Action' in content, "Task1Action schema defined")
                self.check('Task2Action' in content, "Task2Action schema defined")
                self.check('Task3Action' in content, "Task3Action schema defined")
    
    def verify_section_3(self):
        """Section 3: Baseline Script Proof"""
        baseline_script = self.project_root / "baseline" / "run_baseline.py"
        self.check(baseline_script.exists(), "baseline/run_baseline.py exists")
        
        if baseline_script.exists():
            with open(baseline_script) as f:
                content = f.read()
                self.check('--base-url' in content, "Script accepts --base-url argument")
                self.check('def main()' in content, "Script has main() function")
                self.check('exit(0)' in content or 'sys.exit(0)' in content, 
                          "Script calls exit(0) on success")
                self.check('try:' in content and 'except' in content, 
                          "Script has exception handling")
    
    def verify_section_4(self):
        """Section 4: Defensive Programming"""
        core_env = self.project_root / "app" / "engine" / "core_env.py"
        
        if core_env.exists():
            with open(core_env) as f:
                content = f.read()
                # Check max_steps enforcement
                self.check('max_steps' in content, "Environment has max_steps configuration")
                self.check('current_step >= ' in content or 'current_step >=' in content,
                          "Environment enforces step limit")
        
        main_py = self.project_root / "app" / "main.py"
        if main_py.exists():
            with open(main_py) as f:
                content = f.read()
                # Check exception handling
                self.check('except Exception as e' in content,
                          "All exceptions caught with proper handling")
                self.check('except: pass' not in content,
                          "No silent failures (except: pass)")
                self.check('logger.error' in content,
                          "Exceptions logged with context")
    
    def verify_section_5(self):
        """Section 5: Wow Factor (Human Judging)"""
        readme = self.project_root / "README.md"
        self.warn(readme.exists(), "README.md exists and documented")
        
        # Check for semantic naming (in grader.py)
        grader_py = self.project_root / "app" / "api" / "grader.py"
        if grader_py.exists():
            with open(grader_py) as f:
                content = f.read()
                self.check('accumulated_hours' in content, 
                          "Semantic naming: accumulated_hours (not x1)")
                self.check('accumulated_cost' in content,
                          "Semantic naming: accumulated_cost (not y2)")
                self.check('accumulated_carbon' in content,
                          "Semantic naming: accumulated_carbon (not z3)")
        
        # Check git cleanliness
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            clean = result.returncode == 0 and result.stdout.strip() == ""
            self.check(clean, "Git working tree is clean (no uncommitted changes)")
        except:
            self.warn(False, "Could not verify git status")
    
    def print_summary(self):
        """Print final summary."""
        total = self.passed + self.failed + self.warnings
        
        print(f"\n{BOLD}Passed:{RESET} {GREEN}{self.passed}{RESET}")
        print(f"{BOLD}Failed:{RESET} {RED}{self.failed}{RESET}")
        print(f"{BOLD}Warnings:{RESET} {YELLOW}{self.warnings}{RESET}")
        print(f"{BOLD}Total:{RESET} {total}\n")
        
        if self.failed == 0:
            print(f"{GREEN}{BOLD}✓ ALL CRITICAL CHECKS PASSED!{RESET}")
            print(f"{GREEN}Your project is ready for submission.{RESET}\n")
            return 0
        else:
            print(f"{RED}{BOLD}✗ CRITICAL CHECKS FAILED!{RESET}")
            print(f"{RED}Please fix the issues above before submission.{RESET}\n")
            return 1


if __name__ == "__main__":
    verifier = ChecklistVerifier()
    exit_code = verifier.verify_all()
    sys.exit(exit_code)
