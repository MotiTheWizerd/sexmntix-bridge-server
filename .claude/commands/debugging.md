# Debugging Guide

**Audience:** All developers (intermediate to advanced)

**Purpose:** Debugging strategies, systematic investigation, common issues, and problem-solving methodologies.

---

## Key Principles for Debugging

1. **"Demo-first for complex UI"** - Isolate and prove concepts
2. **"Talk before code"** - Clarify the issue before fixing
3. **"Data-driven decisions"** - Use grep/analysis, not assumptions

> **See also:** [general.md](./general.md#key-mantras) for complete mantras list

---

## Systematic Investigation Process

### Step 1: Reproduce

- Create minimal reproduction case
- Document exact steps
- Verify it's consistent
- Note environment details

**Checklist:**
- [ ] Can reproduce on demand
- [ ] Steps documented clearly
- [ ] Environment variables noted
- [ ] Edge cases identified

### Step 2: Trace Data Flow

- Add strategic logging at key points
- Don't log everything - focus on decision points
- Use descriptive log messages
- Track data transformations

**Good logging:**
```typescript
console.log(`State transition: ${oldState} → ${newState}`);
console.log(`Permission data:`, { requestId, toolType, status });
console.log(`Element found:`, !!element, element?.id);
```

**Bad logging:**
```typescript
console.log('here');
console.log(data); // Too vague
console.log('test'); // No context
```

### Step 3: Build Hypothesis

- What do you expect to happen?
- What's actually happening?
- Where's the mismatch?
- What could cause this behavior?

**Framework:**
1. Expected behavior: ___
2. Actual behavior: ___
3. Difference: ___
4. Possible causes: ___

### Step 4: Test Hypothesis

- Make smallest possible change
- Verify impact
- Iterate if needed
- Document findings

---

## Demo-First Development

### When to Use

**Use demo-first for:**
- Complex animations
- Layout issues
- New UI patterns
- Multi-step interactions

**Don't use demo-first for:**
- Simple style tweaks
- Known patterns
- Backend logic
- State management

### The Pattern

**Lesson Learned:** Multiple failed attempts at roll-up animation in production → Built isolated demo in 30 minutes → Success

**Process:**
1. **Isolate the problem** - Create standalone HTML/CSS/JS
2. **Remove variables** - Eliminate framework complexity
3. **Prove the concept** - Get it working in isolation
4. **Integrate carefully** - Port back to production incrementally

**Example Success:**
- Roll-up animation failed 5+ times in production
- Built isolated demo with real CSS
- Discovered scroll container hierarchy issue
- Achieved working animation quickly

### Demo Template

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Copy real CSS here */
    /* Simplify to minimum needed */
  </style>
</head>
<body>
  <div id="test">
    <!-- Minimal HTML structure -->
  </div>
  <script>
    // Minimal JS to test behavior
  </script>
</body>
</html>
```

---

## Common Debug Patterns

### DOM Issues

```javascript
// Add visual markers
element.style.border = '2px solid red';
console.log('Element found:', element);
console.log('Element position:', element.getBoundingClientRect());

// Check if element exists
if (!element) {
  console.error('Element not found with selector:', selector);
  return;
}

// Check element state
console.log('Element classes:', element.className);
console.log('Element computed style:', getComputedStyle(element));
```

### State Issues

```javascript
// Log state transitions
console.log(`State: ${oldState} → ${newState}`);
console.log('State object:', JSON.stringify(stateObject, null, 2));

// Track state changes over time
const stateHistory = [];
function logState(state) {
  stateHistory.push({ state, timestamp: Date.now() });
  console.log('State history:', stateHistory);
}
```

### Event Flow Issues

```javascript
// Trace event propagation
eventBus.on('*', (event, data) => {
  console.log(`Event: ${event}`, data);
});

// Track specific event
let eventCount = 0;
eventBus.on('tool_start', (data) => {
  console.log(`tool_start #${++eventCount}:`, data);
});

// Check event timing
eventBus.on('some_event', (data) => {
  console.log(`Event at ${Date.now()}:`, data);
});
```

---

## Common Gotchas & Solutions

### 1. Over-Abstraction

**Symptom:** 40-line file that exports a single function

**Diagnosis:** Check file structure, look for pure delegation

**Fix:** Consolidate trivial wrappers, keep only meaningful abstractions

> **Related:** See [refactoring.md](./refactoring.md#right-sizing) for refactoring guidance

### 2. ID vs CLASS Collision

**Symptom:** Feature works once, breaks on second use

**Diagnosis:** Check if using IDs for multi-instance elements

**Fix:** Use classes for elements that appear multiple times

**Example:**
```html
<!-- Bad: Breaks on 2nd instance -->
<div id="agent-placeholder"></div>

<!-- Good: Works for all instances -->
<div class="agent-placeholder"></div>
```

### 3. Stale DOM References

**Symptom:** Element operations fail after async operations or tab switches

**Diagnosis:** Check if caching DOM queries

**Fix:** Query DOM right before use, don't cache across async operations

**Pattern:**
```typescript
// Bad: Stale reference
const element = document.querySelector('.target');
await longOperation();
element.update(); // May fail

// Good: Fresh reference
await longOperation();
const element = document.querySelector('.target');
element.update();
```

### 4. State Machine Race Conditions

**Symptom:** Dialog disappears before action completes, flickering states

**Diagnosis:** Check state transition timing

**Fix:** Add intermediate "wait" states for async operations

**Pattern:**
```typescript
// Add wait state
async onUserAction() {
  this.state = 'wait_confirmation';
  this.showFeedback(); // Instant visual feedback
  await this.process();
  this.state = 'completed';
}
```

> **Related:** See [architecture.md](./architecture.md#race-condition-prevention) for prevention patterns

### 5. Event Flow Data Loss

**Symptom:** Data arrives at source but missing at destination

**Diagnosis:** Add logging at each transformation point

**Fix:** Preserve metadata through all transformers

**Debug Pattern:**
```typescript
// Add strategic logging
function transform(data) {
  console.log('Transform input:', data);
  const result = { ...data, transformed: true };
  console.log('Transform output:', result);
  return result;
}
```

### 6. CSS Hardcoded Values

**Symptom:** Styles inconsistent, hard to maintain

**Diagnosis:** Search for duplicate color/spacing values

**Fix:** CSS variables + centralized utilities

**Detection:**
```bash
# Find hardcoded colors
grep -r "#[0-9a-fA-F]\{6\}" styles/

# Find duplicate values
grep -r "rgba(" styles/ | sort | uniq -c | sort -rn
```

> **Related:** See [frontend.md](./frontend.md#css-architecture) for CSS patterns

### 7. Mixed Responsibilities

**Symptom:** File is hard to understand, many imports, long

**Diagnosis:** Count distinct responsibilities (state, UI, events, validation, etc.)

**Fix:** Ultra-modular refactoring with orchestrator pattern

**Detection:**
```bash
# Large files with mixed concerns
find . -name "*.ts" -exec wc -l {} \; | sort -rn | head -10
```

> **Related:** See [refactoring.md](./refactoring.md#when-to-refactor) for refactoring process

### 8. TypeScript Compilation vs Runtime

**Symptom:** Code compiles but crashes at runtime

**Diagnosis:** Check for ESM/CommonJS mismatches, missing runtime dependencies

**Fix:** Test runtime execution, not just compilation

**Debug Steps:**
1. Compile successfully ✓
2. Run the code ✓
3. Test all imports load ✓
4. Verify module resolution ✓

### 9. Premature Implementation

**Symptom:** Built wrong feature, wasted time, user unhappy

**Diagnosis:** Review communication - were requirements clarified?

**Fix:** Talk first, plan second, code third

**Prevention:**
```
User: "I want feature X"
You: "Let me clarify..."
  → Ask questions
  → Confirm understanding
  → Present plan
  → Get approval
  → THEN code
```

> **Related:** See [general.md](./general.md#talk-before-code) for communication patterns

### 10. WebView Caching

**Symptom:** Changes don't appear in WebView UI

**Diagnosis:** Check build output, file timestamps

**Fix:** Reload WebView, verify file paths, check build

**Steps:**
1. Reload WebView (Cmd/Ctrl + R in WebView)
2. Check build output directory
3. Verify file paths match
4. Clear cache if needed
5. Rebuild if necessary

---

## Checklist: Debugging Process

Use this systematic approach for any bug:

- [ ] Reproduced consistently with minimal steps
- [ ] Added strategic logging at decision points
- [ ] Built hypothesis (expected vs actual)
- [ ] Tested hypothesis with smallest change
- [ ] Verified fix doesn't break other features
- [ ] Documented the issue and solution
- [ ] Updated tests if needed

---

## Emergency Debug Patterns

### Find Element Issues
```javascript
// Visual debugging
document.querySelectorAll('.target').forEach(el => {
  el.style.border = '2px solid red';
});

// Check visibility
const isVisible = (el) => {
  return el.offsetWidth > 0 && el.offsetHeight > 0;
};
```

### Trace Event Flow
```javascript
// Event bus tracing
const originalEmit = eventBus.emit;
eventBus.emit = function(event, ...args) {
  console.log(`[EVENT] ${event}`, args);
  return originalEmit.call(this, event, ...args);
};
```

### State Timeline
```javascript
// Track state over time
const timeline = [];
function recordState(label, state) {
  timeline.push({
    time: Date.now(),
    label,
    state: JSON.parse(JSON.stringify(state))
  });
}
```

---

## Related Guides

### For Prevention
- [Architecture Guide](./architecture.md) - Patterns that prevent bugs
- [General Guide](./general.md) - Communication prevents requirements bugs

### For Specific Areas
- [Frontend Guide - CSS](./frontend.md#common-frontend-gotchas) - CSS debugging
- [Backend Guide - State](./backend.md#common-backend-gotchas) - State debugging

### For Evolution
- [Refactoring Guide](./refactoring.md) - Fix root causes through refactoring

---

*Part of the [Semantix Development Guide](../README.md)*
