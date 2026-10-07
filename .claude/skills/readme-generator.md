---
name: readme-generator
description: When creating or updating README.md for a project. Use when asked to "write readme," "create readme," "document this project"
---

# README Generator

Create comprehensive project documentation with these sections:

## Before Writing

### Step 1: Deep Codebase Exploration

**Project Structure**
- Read root directory structure
- Identify framework/language
- Find main entry point(s)
- Map directory organization

**Configuration Files**
- .env.example, environment variables
- pyproject.toml, requirements.txt
- Docker files
- CI/CD configs

**Database**
- Schema files, migrations
- Database type

### Step 2: Identify Deployment Target

Look for: Dockerfile, fly.toml, render.yaml, etc.

## README Structure

### 1. Project Title and Overview
Brief description, 2-3 sentences. Key features list.

### 2. Tech Stack
```markdown
## Tech Stack
- **Language**: Python 3.11+
- **Framework**: LangGraph
- **Scheduling**: OR-Tools, ALNS
- **Database**: PostgreSQL
```

### 3. Prerequisites
What must be installed.

### 4. Getting Started
Complete local development guide with every step.

```markdown
## Getting Started

### 1. Clone the Repository
\`\`\`bash
git clone https://github.com/user/repo.git
cd repo
\`\`\`

### 2. Install Dependencies
\`\`\`bash
uv sync
\`\`\`

### 3. Environment Setup
\`\`\`bash
cp .env.example .env
\`\`\`

### 4. Run Tests
\`\`\`bash
uv run pytest
\`\`\`
```

### 5. Architecture Overview

```markdown
## Architecture

### Directory Structure
\`\`\`
├── agents/
│   ├── gcode-parser/
│   ├── cam-runner/
│   └── cell-scheduler/
├── orchestrator/
├── shared/
└── tests/
\`\`\`

### Data Flow
\`\`\`
G-code → Parser → CAM Analyzer → Scheduler → Production Schedule
\`\`\`
```

### 6. Environment Variables
Complete reference with tables.

### 7. Available Scripts
All commands with descriptions.

### 8. Testing
How to run tests, test structure.

### 9. Deployment
Platform-specific instructions.

### 10. Troubleshooting
Common issues and solutions.

## Writing Principles

1. **Be Absurdly Thorough** - More detail is always better
2. **Use Code Blocks Liberally** - Every command copy-pasteable
3. **Explain the Why** - Not just "run this," but what it does
4. **Assume Fresh Machine** - Reader never saw this codebase
5. **Use Tables for Reference** - Env vars, scripts work great as tables
