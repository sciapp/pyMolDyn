import os


def env_is_true(env_key):
    return os.environ.get(env_key, "0").lower() in ("1", "on", "true", "yes")
