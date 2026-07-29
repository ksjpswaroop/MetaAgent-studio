```markdown
# MetaAgent-studio Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the MetaAgent-studio Python codebase. You'll learn how to structure files, write imports and exports, follow commit conventions, and understand the project's approach to testing. Whether you're contributing new features or reviewing code, these guidelines will help you maintain consistency and quality.

## Coding Conventions

### File Naming
- **Style:** camelCase
- **Example:**  
  ```bash
  agentManager.py
  userProfileHandler.py
  ```

### Import Style
- **Style:** Relative imports
- **Example:**
  ```python
  from .utils import parseConfig
  from .models.agent import Agent
  ```

### Export Style
- **Style:** Named exports (explicitly specifying what is exported)
- **Example:**
  ```python
  __all__ = ['AgentManager', 'UserProfileHandler']
  ```

### Commit Patterns
- **Type:** Conventional Commits
- **Prefix:** `feat`
- **Example:**  
  ```
  feat: add support for multi-agent collaboration in agentManager
  ```

## Workflows

### Feature Development
**Trigger:** When adding a new feature to the codebase  
**Command:** `/feature-development`

1. Create a new branch for your feature.
2. Name new files using camelCase.
3. Use relative imports for internal modules.
4. Export new classes/functions using named exports.
5. Write a commit message starting with `feat:`.
6. Submit a pull request for review.

### Code Review
**Trigger:** When reviewing a pull request  
**Command:** `/code-review`

1. Check that file names use camelCase.
2. Ensure all imports are relative.
3. Verify that exports are named and explicit.
4. Confirm commit messages use the `feat` prefix and are descriptive.
5. Look for corresponding test files if applicable.

## Testing Patterns

- **Framework:** Unknown (no specific framework detected)
- **Test File Pattern:** Files end with `.test.ts`
- **Example:**
  ```
  agentManager.test.ts
  ```
- **Note:** While the main codebase is Python, test files appear to use TypeScript. Ensure tests are placed in files matching the `*.test.ts` pattern.

## Commands
| Command              | Purpose                                      |
|----------------------|----------------------------------------------|
| /feature-development | Step-by-step guide for adding new features   |
| /code-review         | Checklist for reviewing code contributions   |
```
