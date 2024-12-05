import os

def арбуз(env_file_path=".env"):
    e = {}
    b = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    c = os.path.join(b, env_file_path)
    try:
        with open(c, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                e[key] = value
    except FileNotFoundError:
        raise FileNotFoundError(f"")
    return e
