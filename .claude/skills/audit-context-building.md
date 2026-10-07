---
name: audit-context-building
description: Build deep architectural context through ultra-granular code analysis before vulnerability hunting. Use when performing security audits, threat modeling, or architecture reviews.
---

# Audit Context Building

Build deep architectural context through ultra-granular code analysis before vulnerability hunting.

## When to Use

- Develop deep comprehension of a codebase before security auditing
- Build bottom-up understanding instead of high-level guessing
- Reduce hallucinations and context loss during complex analysis
- Prepare for threat modeling or architecture review

## Key Principle

This is a **pure context building** skill. It does NOT:
- Identify vulnerabilities
- Propose fixes
- Generate proofs-of-concept
- Assign severity or impact

It exists solely to build deep understanding before the vulnerability-hunting phase.

## Three Phases

### Phase 1: Initial Orientation

Map the high-level structure:

1. **Modules & Components**
   - List all major modules/packages
   - Identify their responsibilities
   - Note dependencies between them

2. **Entrypoints**
   - HTTP endpoints, CLI commands, message handlers
   - External API surfaces
   - Background job triggers

3. **Actors & Trust Levels**
   - Anonymous users
   - Authenticated users
   - Admins
   - Internal services
   - External integrations

4. **Storage & State**
   - Databases
   - Caches
   - Session stores
   - File systems

### Phase 2: Ultra-Granular Function Analysis

For each critical function:

```
Function: process_order(order_id, user_context)
├── Line 1-5: Input validation
│   ├── What: Validates order_id is integer
│   ├── Why: Prevent injection
│   └── Assumption: order_id comes from trusted source?
├── Line 6-10: Authorization check
│   ├── What: Checks user owns order
│   ├── How: Query orders WHERE user_id = ?
│   └── Gap: No check for order status
├── Line 11-20: Business logic
│   ├── Flow: Load → Transform → Save
│   └── External calls: payment_service.charge()
└── Line 21-25: Response
    └── What data is returned? Sensitive fields?
```

Apply at each block:
- **First Principles**: What is this actually doing?
- **5 Whys**: Why is it done this way?
- **5 Hows**: How could this fail?

### Phase 3: Global System Understanding

Build holistic model:

1. **State & Invariants**
   - What must always be true?
   - What are the consistency requirements?

2. **Workflow Mapping**
   - Complete user journeys
   - State machine transitions

3. **Trust Boundaries**
   - Where does trust change?
   - Where is data sanitized?

## Analysis Template

```markdown
## Module: [name]

### Purpose
[1-2 sentences]

### Dependencies
- Uses: [list]
- Used by: [list]

### Key Functions
| Function | Purpose | Trust Level | Notes |
|----------|---------|-------------|-------|
| func_a   | ...     | user        | ...   |

### Data Flow
[Input] → [Transform] → [Output]

### Invariants
- [ ] Invariant 1
- [ ] Invariant 2

### Open Questions
1. ?
2. ?
```

## Anti-Hallucination Rules

1. **Never reshape evidence** to fit earlier assumptions
2. **Update the model explicitly** when contradicted
3. **Avoid vague guesses** - use "Unclear; need to inspect X"
4. **Cross-reference constantly** to maintain global coherence
5. **Quote exact code** when making claims

## Cross-Function Flow Tracking

When a function calls another:

```
caller() → callee(arg1, arg2)
├── What data flows into callee?
├── What transformations happen?
├── What data flows back?
└── What side effects occur?
```

Track:
- Taint propagation (user input → ?)
- Trust level changes
- Error handling paths
- Resource acquisition/release

## Output

After context building, you should have:

1. **Architecture Map** - Visual or textual representation
2. **Trust Boundary Diagram** - Where trust changes
3. **Data Flow Inventory** - All sensitive data paths
4. **Invariant List** - What must always be true
5. **Open Questions** - Gaps in understanding

Only then proceed to vulnerability hunting.
