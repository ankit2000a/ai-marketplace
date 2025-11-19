import subprocess
import sys
import os

# Default port 8001, strategy budget
cmd = [sys.executable, "-u", "project_manager_agent.py", "--strategy", "budget"]

# If port not in args, add default
if "--port" not in sys.argv:
    cmd.extend(["--port", "8001"])

cmd.extend(sys.argv[1:])

print(f"🚀 Starting PM Budget Variant...")
subprocess.run(cmd)
