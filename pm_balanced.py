import subprocess
import sys
import os

# Default port 8006, strategy balanced
cmd = [sys.executable, "-u", "project_manager_agent.py", "--strategy", "balanced"]

# If port not in args, add default
if "--port" not in sys.argv:
    cmd.extend(["--port", "8006"])

cmd.extend(sys.argv[1:])

print(f"🚀 Starting PM Balanced Variant...")
subprocess.run(cmd)
