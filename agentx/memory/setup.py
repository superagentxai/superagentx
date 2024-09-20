import json
import os
import uuid

# Set up the directory path
home_dir = os.path.expanduser("~")
mem_dir = os.environ.get("MEMORY_DIR") or os.path.join(home_dir, ".agentx_mem")
os.makedirs(mem_dir, exist_ok=True)