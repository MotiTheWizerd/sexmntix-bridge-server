
import sys
import os

print("Starting debug_imports.py...", file=sys.stderr)

def trace_prints(frame, event, arg):
    if event == 'call':
        return trace_prints
    if event == 'line':
        return trace_prints
    return trace_prints

# We can't easily intercept C-level print() calls, but we can redirect stdout
import io
original_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    print("Importing src.modules.xcp_server...", file=sys.stderr)
    import src.modules.xcp_server
    print("Import complete.", file=sys.stderr)
except Exception as e:
    print(f"Import failed: {e}", file=sys.stderr)

captured = sys.stdout.getvalue()
sys.stdout = original_stdout

if captured:
    print(f"CAPTURED STDOUT DURING IMPORT:\n{captured}", file=sys.stderr)
    print("FOUND THE CULPRIT! Something printed during import.", file=sys.stderr)
else:
    print("No stdout output captured during import.", file=sys.stderr)
