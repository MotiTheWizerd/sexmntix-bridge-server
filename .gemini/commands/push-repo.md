# AI Agent Git Workflow Instructions

## Step 1: Git Stability Check Instructions
**Before executing `git add .`, always:**

1. **Run `git status --porcelain`** - Check the output:
   - If you see `UU`, `AA`, `DD` patterns → Stop, respond: "Merge conflicts detected, resolve manually first"
   - If output is empty → Stop, respond: "No changes to commit"

2. **Check for ongoing operations:**
   - Run `git status` and look for phrases like "rebase in progress", "merge in progress"
   - If found → Stop, respond: "Git operation in progress, complete it first"

3. **Verify you're in a git repo:**
   - Run `git rev-parse --git-dir`
   - If it errors → Stop, respond: "Not in a git repository"

4. **Only if all checks pass → Execute `git add .`**

## Step 2: Commit Message Generation
**After successful `git add .`:**

1. **Get the diff data:** `git diff --cached --stat`
2. **Analyze the changes** and create commit message following this pattern:
   - Start with action verb (Add, Fix, Update, Remove, etc.)
   - Be specific about what changed
   - Keep first line under 50 characters
   - Add details in body if needed

3. **Execute:** `git commit -m "your generated message"`

## Step 3: Push to GitHub
**After successful commit:**

1. **Check remote exists:** `git remote get-url origin`
   - If it errors → Stop, respond: "No origin remote configured"

2. **Get current branch:** `git branch --show-current`
3. **Execute push:** `git push origin [branch-name]`
4. **Check push result** - if it fails, report the specific error

## Critical Rule
**Stop immediately at first failure and report the exact reason. Never continue to next step if previous step failed.**
