# Refactoring Guide

**Audience:** Developers working on legacy/existing code

**Purpose:** Code evolution, modularization patterns, and maintenance strategies.

---

## Key Principles for Refactoring

1. **"Right-size, don't over-abstract"** - Balance is key
2. **"Talk before code"** - Clarify scope before refactoring
3. **"Backwards compatible always"** - Zero breaking changes
4. **"Data-driven decisions"** - Use grep/analysis, not assumptions

> **See also:** [general.md](./general.md#key-mantras) for complete mantras list

---

## When to Refactor

### Refactor When You See:

1. **Mixed responsibilities** (3+ distinct concerns in one file)
   - Example: File handles initialization + state + events + validation
   - Detection: Count import types (filesystem, UI, events, state)

2. **Code duplication** (same logic in multiple places)
   - Example: Same validation in 5 different files
   - Detection: `grep -r "specificPattern" | wc -l`

3. **Files over 200 lines** with complex logic
   - Example: 400-line monolithic component
   - Detection: `find . -name "*.ts" -exec wc -l {} \; | awk '$1 > 200'`

4. **Scattered inline logic** that could be extracted
   - Example: Complex calculations repeated inline
   - Detection: Look for duplicate code blocks

### Don't Refactor When:

1. **File is already focused and small** (<100 lines, single responsibility)
2. **Logic is truly one-off** and won't be reused
3. **You're creating abstraction "just in case"**
4. **No clear improvement** to maintainability

**Key Question:** Will this make the code easier to understand and maintain?

> **Related:** See [architecture.md](./architecture.md#right-sizing-evolution) for philosophy

---

## Ultra-Modular Refactoring Pattern

### The Process

**Step 1: Analysis**
- Use `grep` to find all usages
- Identify responsibility clusters
- Map dependencies and coupling
- Document current pain points

**Analysis Commands:**
```bash
# Find all usages
grep -r "ClassName" src/

# Find imports
grep -r "import.*ClassName" src/

# Count lines by concern
grep -c "useState\|useEffect" ComponentFile.tsx
grep -c "eventBus\|emit" ComponentFile.tsx
```

**Step 2: Design**
- Create orchestrator for coordination
- Design micro-components for specific tasks
- Plan dependency injection approach
- Sketch new structure

**Design Template:**
```
Feature/
├── Orchestrator.ts      # 120-200 lines
├── components/
│   ├── subsystem-a/     # Related components
│   │   ├── Component1.ts
│   │   └── Component2.ts
│   └── subsystem-b/
│       └── Component3.ts
└── types.ts
```

**Step 3: Implementation**
- Build components incrementally
- Maintain backward compatibility (zero breaking changes)
- Test at each step
- Keep old code working during transition

**Implementation Pattern:**
```typescript
// Step 1: Create new components (don't touch old code)
// Step 2: Create orchestrator using new components
// Step 3: Add orchestrator alongside old code
// Step 4: Gradually migrate callers
// Step 5: Remove old code when nothing uses it
```

**Step 4: Validation**
- Verify all original functionality works
- Check for performance impact
- Review for over-abstraction
- Ensure backward compatibility

**Validation Checklist:**
- [ ] All tests pass
- [ ] No new bugs introduced
- [ ] Performance same or better
- [ ] No breaking changes to API
- [ ] Not over-abstracted

---

## Component Organization

### Typical Subsystem Structure

```
feature/
├── FeatureOrchestrator.ts          # Main coordinator
├── components/
│   ├── initialization/             # Startup logic
│   │   ├── Bootstrapper.ts
│   │   └── ConfigLoader.ts
│   ├── state/                      # State management
│   │   ├── StateManager.ts
│   │   └── CacheManager.ts
│   └── operations/                 # Business logic
│       ├── OperationA.ts
│       └── OperationB.ts
└── types.ts                        # Shared interfaces
```

**Organization Principles:**
- Group by cohesion (related components together)
- Each component 25-50 lines
- Single responsibility per file
- Shared types in types.ts
- Clear subsystem boundaries

> **Related:** See [architecture.md](./architecture.md#component-organization-patterns) for architecture details

---

## Orchestrator Pattern

### Theory

> **Architecture Note:** For detailed pattern theory, see [architecture.md](./architecture.md#orchestrator-pattern).

**Core Idea:** Thin orchestrator coordinates focused micro-components.

### Implementation

**Orchestrator Responsibilities:**
- Initialize dependencies
- Coordinate component calls
- Manage lifecycle
- Handle errors

**Orchestrator Does NOT:**
- Implement business logic
- Duplicate component code
- Handle detailed operations

**Example:**
```typescript
class FeatureOrchestrator {
  constructor(
    private bootstrapper: Bootstrapper,
    private stateManager: StateManager,
    private operations: Operations
  ) {}

  async initialize() {
    // Coordinate, don't implement
    await this.bootstrapper.setup();
    this.stateManager.init();
  }

  async process(request) {
    // Coordinate workflow
    const state = this.stateManager.get();
    const result = await this.operations.execute(request, state);
    this.stateManager.update(result.newState);
    return result;
  }
}
```

### Micro-Components

**Component Characteristics:**
- 25-50 lines average
- Single responsibility
- No dependencies on siblings
- Testable in isolation

**Example:**
```typescript
// Good: Focused component
class ConfigLoader {
  load(path: string): Config {
    // Single responsibility: load config
    const raw = fs.readFileSync(path);
    return JSON.parse(raw);
  }
}

// Bad: Mixed responsibilities
class ConfigLoaderAndValidator {
  loadAndValidateAndTransform(path: string): ProcessedConfig {
    // Too many responsibilities
  }
}
```

---

## Right-Sizing: Avoiding Over-Abstraction

### Warning Signs

1. **40-line file for 1-line operation**
   ```typescript
   // Over-abstracted
   export class StringUppercaser {
     uppercase(str: string): string {
       return str.toUpperCase();
     }
   }
   ```

2. **Pure delegation layers**
   ```typescript
   // Just delegates, no logic
   export class UserFacade {
     getUser(id) {
       return userRepository.findById(id);
     }
   }
   ```

3. **100% dead code**
   ```typescript
   // Export never imported anywhere
   export class UnusedHelper {
     // Nobody calls this
   }
   ```

### Detection

```bash
# Find tiny files
find . -name "*.ts" -exec wc -l {} \; | awk '$1 < 50' | sort -n

# Find unused exports
grep -r "export class" src/ > exports.txt
grep -r "import.*from" src/ > imports.txt
# Compare manually

# Find single-function files
grep -c "^export function" src/**/*.ts | grep ":1$"
```

### Fix

**Consolidate when:**
- Component is pure delegation
- Component has single trivial operation
- Component is never actually used
- Abstraction adds no value

**Keep when:**
- Component has real logic
- Component will be reused
- Abstraction clarifies design
- Testing benefits from isolation

---

## Common Refactoring Gotchas

### Over-Abstraction

**Problem:** Creating components "just in case"

**Fix:** Only extract when you have 2+ real use cases

> **Related:** See [architecture.md](./architecture.md#right-sizing-evolution) for philosophy

### Mixed Responsibilities

**Problem:** One file handles too many concerns

**Fix:** Ultra-modular refactoring with orchestrator pattern

**Detection:**
```typescript
// Mixed concerns
class ChatManager {
  // Database operations
  saveMessage(msg) { }

  // UI updates
  renderMessage(msg) { }

  // Business logic
  processMessage(msg) { }

  // Networking
  sendToServer(msg) { }
}
```

**Solution:**
```typescript
// Separated
class ChatOrchestrator {
  constructor(
    private db: MessageRepository,
    private ui: MessageRenderer,
    private processor: MessageProcessor,
    private network: NetworkClient
  ) {}
}
```

### Premature Refactoring

**Problem:** Refactoring before understanding requirements

**Fix:** Talk first, understand scope, then refactor

**Pattern:**
1. Identify the problem
2. Discuss with team/user
3. Agree on scope
4. Plan approach
5. Then refactor

> **Related:** See [general.md](./general.md#talk-before-code) for communication

---

## Refactoring Checklist

Use before starting any refactoring:

- [ ] Identified clear problem (duplication, mixed concerns, complexity)
- [ ] Analyzed current code structure (grep, usage analysis)
- [ ] Designed new structure (orchestrator + components)
- [ ] Plan maintains backward compatibility
- [ ] Have tests to verify no regressions
- [ ] Incremental approach planned
- [ ] Know when to stop (avoid over-abstraction)

---

## Real-World Examples

### Example 1: ConversationProcessor

**Before:** 254 lines with 4x agent state duplication

**After:** 145-line orchestrator + 23 focused micro-components

**Key Improvements:**
- Zero code duplication
- Clear separation of concerns
- Easier to test
- Easier to maintain

### Example 2: ChatInstance

**Before:** 216 lines with mixed responsibilities (initialization, lifecycle, state, events)

**After:** Orchestrator + 17 micro-components in 4 subsystems

**Subsystems:**
- Initialization (bootstrapping, config)
- State (state management, caching)
- Lifecycle (startup, shutdown)
- Events (event handling, emission)

### Example 3: CSS Refactoring

**Before:** 446-line monolithic `header-dropdown.css`

**After:** 67-line orchestrator + 5 focused CSS modules

**Result:** 87% size reduction, zero hardcoded values, reusable utilities

> **Related:** See [frontend.md](./frontend.md#css-architecture) for CSS patterns

---

## Related Guides

### For Architecture Understanding
- [Architecture Guide](./architecture.md) - Pattern theory and design
- [Architecture Guide - Orchestrator](./architecture.md#orchestrator-pattern)

### For Implementation
- [Backend Guide](./backend.md) - Backend refactoring examples
- [Frontend Guide](./frontend.md) - CSS refactoring examples

### For Validation
- [Debugging Guide](./debugging.md) - Verify refactoring didn't break anything
- [General Guide - Testing](./general.md#testing-strategy)

---

*Part of the [Semantix Development Guide](../README.md)*
