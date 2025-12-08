
import sys
import os
import io

# 1. Force unbuffered stdin/stdout
# On Windows, we need to ensure binary mode or unbuffered text mode.
# Python's -u flag does this, but let's be explicit if we can.
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# 2. REDIRECT STDERR to a file immediately
# This prevents ANY library import warnings from corrupting the stream
with open("mcp_boot_stderr.log", "w") as f:
    sys.stderr = f
    
    # 3. Import and run
    try:
        from src.modules.xcp_server.__main__ import cli_main
        cli_main()
    except Exception as e:
        # If we fail, try to write to the log file we just opened (sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
