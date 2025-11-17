#!/usr/bin/env python3
"""
Intelligent Version Control Assistant

Provides voice-controlled git operations with AI-powered commit messages,
PR descriptions, and conflict resolution.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GitAssistant:
    """Voice-controlled git operations"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def _run_git(self, args: List[str]) -> Tuple[bool, str, str]:
        """Run git command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path)] + args,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def get_staged_diff(self) -> str:
        """Get diff of staged changes"""
        success, diff, _ = self._run_git(["diff", "--staged"])
        return diff if success else ""

    def get_unstaged_diff(self) -> str:
        """Get diff of unstaged changes"""
        success, diff, _ = self._run_git(["diff"])
        return diff if success else ""

    def get_status(self) -> Dict:
        """Get git status"""
        success, output, _ = self._run_git(["status", "--porcelain"])
        if not success:
            return {"error": "Failed to get git status"}

        staged = []
        unstaged = []
        untracked = []

        for line in output.split("\n"):
            if not line:
                continue

            status = line[:2]
            file_path = line[3:]

            if status[0] != " " and status[0] != "?":
                staged.append(file_path)
            if status[1] != " ":
                unstaged.append(file_path)
            if status[0] == "?":
                untracked.append(file_path)

        return {
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
        }

    def generate_commit_message(
        self,
        diff: str,
        message_type: str = "conventional",
    ) -> str:
        """
        Generate commit message from diff

        This is a simplified version. In production, this would call Claude API
        to generate semantic commit messages.
        """
        # Extract changed files
        files_changed = set()
        for line in diff.split("\n"):
            if line.startswith("+++") or line.startswith("---"):
                file_path = line[6:]  # Remove "+++ b/" or "--- a/"
                if file_path and file_path != "/dev/null":
                    files_changed.add(file_path)

        if not files_changed:
            return "chore: update files"

        # Detect scope from file paths
        scope = "app"
        for file_path in files_changed:
            if "test" in file_path.lower():
                scope = "test"
                break
            elif "doc" in file_path.lower():
                scope = "docs"
                break
            elif "config" in file_path.lower() or file_path.endswith(".json") or file_path.endswith(".yaml"):
                scope = "config"
                break
            elif any(ext in file_path for ext in [".py", ".js", ".ts"]):
                # Try to extract module name
                parts = file_path.split("/")
                if len(parts) > 1:
                    scope = parts[-2]
                break

        # Detect type from diff content
        commit_type = "chore"
        additions = 0
        deletions = 0

        for line in diff.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                additions += 1
                if "def " in line or "class " in line or "function " in line:
                    commit_type = "feat"
                elif "fix" in line.lower() or "bug" in line.lower():
                    commit_type = "fix"
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1

        # If mostly deletions, it's likely a refactor
        if deletions > additions * 1.5:
            commit_type = "refactor"

        # Build commit message
        subject = f"{commit_type}({scope}): update implementation"

        body = f"""
Modified files:
{chr(10).join('- ' + f for f in sorted(files_changed))}

Changes: +{additions} -{deletions}
"""

        return f"{subject}\n{body.strip()}"

    def smart_commit(
        self,
        auto_message: bool = True,
        custom_message: Optional[str] = None,
    ) -> Dict:
        """Commit with AI-generated or custom message"""
        # Check for staged changes
        status = self.get_status()
        if not status.get("staged"):
            return {"error": "No staged changes to commit"}

        # Generate or use message
        if custom_message:
            message = custom_message
        elif auto_message:
            diff = self.get_staged_diff()
            message = self.generate_commit_message(diff)
        else:
            return {"error": "No commit message provided"}

        # Commit
        success, stdout, stderr = self._run_git(["commit", "-m", message])

        if success:
            # Get commit hash
            success_hash, commit_hash, _ = self._run_git(["rev-parse", "--short", "HEAD"])
            return {
                "status": "committed",
                "hash": commit_hash.strip() if success_hash else "unknown",
                "message": message,
            }
        else:
            return {"error": stderr or "Commit failed"}

    def create_branch(
        self,
        name: str,
        branch_type: str = "feature",
    ) -> Dict:
        """Create and checkout new branch"""
        # Format branch name
        if not name.startswith(f"{branch_type}/"):
            branch_name = f"{branch_type}/{name}"
        else:
            branch_name = name

        # Create branch
        success, _, stderr = self._run_git(["checkout", "-b", branch_name])

        if success:
            return {
                "status": "created",
                "branch": branch_name,
            }
        else:
            return {"error": stderr or "Failed to create branch"}

    def generate_pr_description(
        self,
        base_branch: str = "main",
    ) -> Dict:
        """
        Generate PR description from commits

        This is a simplified version. In production, this would call Claude API
        to generate comprehensive PR descriptions.
        """
        # Get current branch
        success, current_branch, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if not success:
            return {"error": "Failed to get current branch"}

        current_branch = current_branch.strip()

        # Get commits ahead of base branch
        success, commits, _ = self._run_git(["log", f"{base_branch}..HEAD", "--oneline"])
        if not success:
            return {"error": "Failed to get commits"}

        # Get changed files
        success, files, _ = self._run_git(["diff", f"{base_branch}...HEAD", "--name-only"])
        if not success:
            return {"error": "Failed to get changed files"}

        # Parse commits
        commit_lines = [line for line in commits.split("\n") if line]

        # Generate title from branch name or first commit
        title = current_branch.replace("-", " ").replace("_", " ").title()
        if "/" in title:
            title = title.split("/", 1)[1]

        # Generate description
        description = f"""## Summary

This PR includes the following changes:

"""

        # Add commit list
        if commit_lines:
            description += "## Commits\n\n"
            for commit in commit_lines[:10]:  # Limit to 10 commits
                description += f"- {commit}\n"

        # Add changed files
        file_list = [f for f in files.split("\n") if f]
        if file_list:
            description += f"\n## Files Changed ({len(file_list)})\n\n"
            for file_path in file_list[:20]:  # Limit to 20 files
                description += f"- {file_path}\n"

        description += """
## Test Plan

- [ ] Unit tests passing
- [ ] Manual testing completed
- [ ] Documentation updated

## Related Issues

Closes #
"""

        return {
            "title": title,
            "description": description,
            "base_branch": base_branch,
            "head_branch": current_branch,
        }

    def detect_conflicts(self) -> Dict:
        """Detect merge conflicts"""
        success, output, _ = self._run_git(["diff", "--name-only", "--diff-filter=U"])

        if not success:
            return {"conflicts": []}

        conflicted_files = [f for f in output.split("\n") if f]

        return {
            "has_conflicts": len(conflicted_files) > 0,
            "files": conflicted_files,
        }

    def analyze_conflict(self, file_path: str) -> Dict:
        """
        Analyze merge conflict in file

        This is a simplified version. In production, this would call Claude API
        to analyze and suggest resolutions.
        """
        try:
            with open(self.repo_path / file_path) as f:
                content = f.read()
        except Exception as e:
            return {"error": str(e)}

        # Parse conflict markers
        conflicts = []
        in_conflict = False
        current_conflict = {"ours": [], "theirs": [], "base": []}
        section = ""

        for line_num, line in enumerate(content.split("\n"), 1):
            if line.startswith("<<<<<<<"):
                in_conflict = True
                section = "ours"
                current_conflict = {"ours": [], "theirs": [], "base": [], "line": line_num}
            elif line.startswith("======="):
                section = "theirs"
            elif line.startswith(">>>>>>>"):
                in_conflict = False
                conflicts.append(current_conflict)
                section = ""
            elif in_conflict and section:
                current_conflict[section].append(line)

        return {
            "file": file_path,
            "conflicts": len(conflicts),
            "details": conflicts,
        }

    def pull_changes(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
    ) -> Dict:
        """Pull changes from remote"""
        args = ["pull", remote]
        if branch:
            args.append(branch)

        success, output, stderr = self._run_git(args)

        if success:
            # Check for conflicts
            conflicts = self.detect_conflicts()
            return {
                "status": "pulled",
                "output": output,
                "conflicts": conflicts,
            }
        else:
            return {"error": stderr or "Pull failed"}

    def push_changes(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
    ) -> Dict:
        """Push changes to remote"""
        args = ["push"]

        if force:
            args.append("--force")

        args.extend(["-u", remote])

        if branch:
            args.append(branch)

        success, output, stderr = self._run_git(args)

        if success:
            return {
                "status": "pushed",
                "output": output,
            }
        else:
            return {"error": stderr or "Push failed"}


class CommitMessageGenerator:
    """Generate semantic commit messages"""

    @staticmethod
    def generate(diff: str, style: str = "conventional") -> str:
        """
        Generate commit message from diff

        This is a placeholder. In production, this would call Claude API.
        """
        git_assistant = GitAssistant()
        return git_assistant.generate_commit_message(diff, style)


class PRDescriptionGenerator:
    """Generate PR descriptions"""

    @staticmethod
    def generate(base_branch: str = "main") -> Dict:
        """
        Generate PR description

        This is a placeholder. In production, this would call Claude API.
        """
        git_assistant = GitAssistant()
        return git_assistant.generate_pr_description(base_branch)


class ConflictResolver:
    """Analyze and resolve merge conflicts"""

    @staticmethod
    def analyze(file_path: str) -> Dict:
        """
        Analyze conflict

        This is a placeholder. In production, this would call Claude API.
        """
        git_assistant = GitAssistant()
        return git_assistant.analyze_conflict(file_path)
