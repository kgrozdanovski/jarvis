#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import signal

# Signal handler for graceful shutdown
signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))


def remove_quotes(s):
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def load_env():
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    env_file_path = os.path.join(current_file_dir, "..", "..", ".env")

    if os.path.exists(env_file_path):
        with open(env_file_path, encoding="utf8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                # If the value is encapsulated in double quotes, remove them

                key, value = line.strip().split('=', 1)
                os.environ[key] = remove_quotes(value)

    os.environ['PROJECT_ROOT'] = os.path.join(current_file_dir, '..')
    os.environ['PYTHONIOENCODING'] = 'UTF-8'


def execute(cmd):
    popen = subprocess.Popen(
        cmd,
        env=subprocessEnvironment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # Add stderr capture
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        error_output = popen.stderr.read() if popen.stderr else "No error output captured"
        raise subprocess.CalledProcessError(return_code, cmd, stderr=error_output)


current_file_dir = os.path.dirname(os.path.abspath(__file__))

if os.getenv('DOCKER') is True:
    os.environ['PROJECT_ROOT'] = os.getenv('DOCKER_PROJECT_ROOT')
else:
    os.environ['PROJECT_ROOT'] = os.path.join(current_file_dir, "..", "..")

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", help="The script name", required=True)

CONSOLE_ARGS, subprocess_args = parser.parse_known_args()

script_name = CONSOLE_ARGS.name
if not script_name:
    print("No script name provided. Exiting.")
    sys.exit(1)

script_path = os.path.join(current_file_dir, script_name + '.py')
if not os.path.isfile(script_path):
    print(f"Script '{script_path}' not found in the configured scripts directory. Exiting.")
    sys.exit(1)

print("Loading environment for subprocess...")

load_env()

subprocessEnvironment = os.environ.copy()
subprocessEnvironment["PYTHONPATH"] = f"{os.environ['PROJECT_ROOT']}"

try:
    print(f"Executing script: {script_path}")
    # Use sys.executable to get the path of the current Python interpreter
    # This ensures we use the same Python interpreter (and thus the same virtual env)
    for line in execute([sys.executable, "-u", script_path, *subprocess_args]):
        print(line, end="")
except subprocess.CalledProcessError as e:
    print(f"Error executing script: {e}")
    if hasattr(e, 'stderr'):
        print(f"Error output: {e.stderr}")
    sys.exit(1)
except KeyboardInterrupt:   # Handle CTRL+C gracefully
    print("Script interrupted by user.")
    sys.exit(0)
