# General Development Practices

**Audience:** All developers regardless of specialization

**Purpose:** Core principles, workflows, and practices that apply to everyone on the Semantix team.

---

## Key Principles

1. **"Talk before code"** - Always clarify requirements first
2. **"Memory-guided development"** - Learn from past work
3. **"Plan-first methodology"** - Research, plan, then implement
4. **"Backwards compatible always"** - Zero breaking changes

> **See also:** [Complete mantras list](#key-mantras)

---

## Communication & Planning

### The "Talk Before Code" Rule

**Anti-Pattern:** Jump into implementation without understanding requirements

**Example Failure:**
- User: "I want provider-specific working text patterns"
- Agent: Immediately implements solution
- Result: Built wrong feature, wasted time

**Correct Pattern:**
1. **Ask clarifying questions** - "What specific patterns do you want?"
2. **Confirm understanding** - "So you want X, Y, Z?"
3. **Plan approach** - "I'll do it this way..."
4. **Get approval** - Wait for confirmation
5. **Then implement** - Code with confidence

### Requirements Gathering

**Critical Rule:** Never assume. Always clarify.

**Good Questions:**
- "What specific behavior do you want?"
- "How should it work when [edge case]?"
- "Do you want [option A] or [option B]?"
- "Can you show me an example?"

**Bad Questions:**
- "Is this what you want?" (while showing already-built solution)

### Progress Communication

**Pattern:**
1. Acknowledge request
2. Explain approach
3. Show progress incrementally
4. Highlight key decisions
5. Report completion with summary

**Example:**
```
User: "Add dark mode toggle"

Response:
"I'll add a dark mode toggle to settings. Here's my plan:
1. Create toggle component in Settings
2. Add state management (context/store)
3. Implement CSS-in-JS styles
4. Update components to support theme switching

Starting with step 1..."
```

### Managing Complexity

**When to ask for help:**
- Multiple valid approaches exist
- Unclear requirements
- Breaking changes might be needed
- Design decision affects architecture

**When to proceed:**
- Requirements are clear
- Pattern is proven
- Backward compatible
- Low risk

---

## Development Workflow

### Plan-First Methodology

**Pattern for Complex Features:**

1. **Research Phase**
   - Search semantic memory for related work
   - Read relevant code sections
   - Understand current architecture

2. **Planning Phase**
   - Break down into subtasks
   - Identify dependencies
   - Design component structure
   - **Get user approval before coding**

3. **Implementation Phase**
   - Build incrementally
   - Test after each component
   - Maintain backward compatibility

4. **Validation Phase**
   - Verify all requirements met
   - Check for regressions
   - Update documentation

### Memory-Guided Development

**Use Semantic Memory:**
```typescript
// Before implementing new feature
search_memory("similar feature pattern")
search_memory_by_date("recent architecture decisions", timePeriod: "recent")

// Learn from past mistakes
search_memory("failed approach component-name")

// Find proven patterns
search_memory("ultra-modular refactoring pattern")
```

**Why This Matters:**
- Avoid repeating past mistakes
- Discover proven patterns
- Understand architectural decisions
- Learn from successful implementations

### Testing Strategy

**Key Principles:**
1. **Test in isolation first** (demo-first development)
2. **Test integration points** (event flow, state transitions)
3. **Test edge cases** (multi-tab, multi-turn, race conditions)
4. **Test backward compatibility** (existing features still work)

> **Related:** See [debugging.md](./debugging.md#demo-first-development) for demo-first testing approach

---

## Universal Best Practices

### Code Quality
- **Single Responsibility** - One component, one purpose
- **No Duplication** - Extract shared logic
- **Backward Compatible** - Never break existing functionality
- **Clear Naming** - Self-documenting code

### Architecture Awareness
- **Event-Driven** - Decouple components where appropriate
- **State Management** - Keep state clear and predictable
- **Error Handling** - Always handle edge cases
- **Logging** - Add strategic logging for debugging

> **See also:**
> - [architecture.md](./architecture.md) - System design principles
> - [refactoring.md](./refactoring.md) - When to evolve code

### Documentation
- **Code Comments** - Explain "why", not "what"
- **Update Docs** - Keep documentation in sync with code
- **Memory Logs** - Record important decisions
- **Examples** - Provide usage examples

---

## Checklist: Communication

Use this before starting any non-trivial task:

- [ ] Requirements clarified with user
- [ ] Approach explained and approved
- [ ] Plan documented (for complex features)
- [ ] Progress updates provided during work
- [ ] Completion summary given with results

---

## Key Mantras

1. **"Talk before code"** - Always clarify requirements first
2. **"Demo-first for complex UI"** - Isolate and prove concepts
3. **"Right-size, don't over-abstract"** - Balance is key
4. **"Event-driven for decoupling"** - Components shouldn't know each other
5. **"Orchestrators coordinate, components execute"** - Clear separation
6. **"Stream everything"** - Never block the UI
7. **"Independent state tracks"** - Don't mix unrelated states
8. **"Backwards compatible  ASK"** - Always ask if we need backwards compatiblilty
9. **"Memory-guided development"** - Learn from past work
10. **"Data-driven decisions"** - Use grep/analysis, not assumptions

---

## Related Guides

### For Specific Roles
- [Architecture Guide](./architecture.md) - System design and patterns
- [Frontend Guide](./frontend.md) - UI/UX implementation
- [Backend Guide](./backend.md) - Extension core logic

### For Specific Tasks
- [Debugging Guide](./debugging.md) - Troubleshooting methodology
- [Refactoring Guide](./refactoring.md) - Code evolution

### For Quick Reference
- [Quick Instructions](../quick-instructions.md) - Fast reference format
- [Complete Guide](../semantix_general_guide.md) - Comprehensive documentation

---

*Part of the [Semantix Development Guide](../README.md)*
