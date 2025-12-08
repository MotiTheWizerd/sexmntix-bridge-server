"""
Test if stdin is readable
"""
import sys

print("Testing stdin...", file=sys.stderr)
print(f"stdin.isatty(): {sys.stdin.isatty()}", file=sys.stderr)
print(f"stdin.readable(): {sys.stdin.readable()}", file=sys.stderr)

# Try to read one byte
try:
    import select
    if select.select([sys.stdin], [], [], 0)[0]:
        print("stdin has data available", file=sys.stderr)
    else:
        print("stdin has NO data available", file=sys.stderr)
except Exception as e:
    print(f"select failed: {e}", file=sys.stderr)

print("READY", flush=True)  # This goes to stdout for MCP

# Wait for input
try:
    line = sys.stdin.readline()
    print(f"Read from stdin: {line}", file=sys.stderr)
except Exception as e:
    print(f"Failed to read stdin: {e}", file=sys.stderr)
