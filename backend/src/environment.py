import os


def remove_quotes(s):
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    return s


def is_dev():
    return os.getenv('APP_ENV') == 'dev'


current_file_dir = os.path.dirname(os.path.abspath(__file__))

# Set the PROJECT_ROOT depending on weather or not we are inside a Docker container
if os.getenv('DOCKER') is True:
    os.environ['PROJECT_ROOT'] = os.getenv('DOCKER_PROJECT_ROOT')
else:
    os.environ['PROJECT_ROOT'] = os.path.join(current_file_dir, "..", "..")

env_file_path = os.path.join(os.environ['PROJECT_ROOT'], ".env")

if os.path.exists(env_file_path):
    with open(env_file_path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            # If the value is encapsulated in double quotes, remove them
            key, value = line.strip().split('=', 1)
            os.environ[key] = remove_quotes(value)

os.environ['PROJECT_ROOT'] = os.path.join(current_file_dir, '..')
