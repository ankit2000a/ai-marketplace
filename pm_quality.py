import subprocess
import sys
import os

# Default port 8005, strategy quality
cmd = [sys.executable, "-u", "project_manager_agent.py", "--strategy", "quality"]

# If port not in args, add default
if "--port" not in sys.argv:
    cmd.extend(["--port", "8005"])

cmd.extend(sys.argv[1:])

print(f"🚀 Starting PM Quality Variant...")
subprocess.run(cmd)
