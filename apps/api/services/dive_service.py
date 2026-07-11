import subprocess
import re

# Loosely validates a Docker image reference before we ever shell out to dive/docker.
# Not a full spec implementation (Docker's real grammar is more permissive around
# registry hosts/ports) — this is just enough to reject obviously malformed input
# (empty strings, whitespace, shell-hostile characters) with a clear message instead
# of a generic downstream failure.
IMAGE_REFERENCE_PATTERN = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?'          # first path segment
    r'(/[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?)*'        # optional further path segments
    r'(:[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127})?'               # optional :tag
    r'(@sha256:[a-fA-F0-9]{64})?$'                         # optional @digest
)


def is_valid_image_reference(image_name):
    if not image_name or not isinstance(image_name, str):
        return False
    if len(image_name) > 255:
        return False
    return bool(IMAGE_REFERENCE_PATTERN.match(image_name.strip()))


def _friendly_dive_error(stderr, image_name):
    text = (stderr or '').strip()
    lower = text.lower()

    if 'pull access denied' in lower or 'repository does not exist' in lower:
        return (
            f"Image '{image_name}' wasn't found (or is private). "
            "Double-check the name/tag, or make sure the host running LayerLens "
            "is logged in if it's a private image."
        )
    if 'manifest unknown' in lower or ('manifest for' in lower and 'not found' in lower):
        return f"That tag doesn't exist for '{image_name}'. Check the tag and try again."
    if 'no such host' in lower or 'dial tcp' in lower or 'lookup' in lower:
        return "Couldn't reach the image registry (network error) from the LayerLens backend."
    if 'unauthorized' in lower:
        return f"Access to '{image_name}' was denied — it may be a private image requiring credentials."
    if 'invalid reference format' in lower:
        return f"'{image_name}' isn't a valid image reference."

    # Fallback: surface the last non-empty line dive/docker printed, truncated.
    last_line = next((line for line in reversed(text.splitlines()) if line.strip()), 'Unknown error')
    return last_line[:300]


def analyze_docker_image(image_name):
    if not is_valid_image_reference(image_name):
        return {'error': f"'{image_name}' doesn't look like a valid image reference (expected something like 'repo/name:tag')."}

    print(f"Running Dive against {image_name}")
    try:
        result = subprocess.run(
            ['dive', image_name, '--ci'],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except FileNotFoundError:
        return {'error': "The 'dive' CLI isn't available on the analysis server."}
    except subprocess.TimeoutExpired:
        return {'error': f"Analyzing '{image_name}' timed out after 180 seconds."}

    if result.returncode != 0:
        print("Error running Dive:", result.stderr)
        return {'error': _friendly_dive_error(result.stderr, image_name)}

    stats = parse_dive_output(result.stdout)
    return {
        'image_name': image_name,
        'stats': stats,
        'output': result.stdout,
    }


def parse_dive_output(output):
    # Regular expressions to capture the required values
    efficiency_pattern = r'efficiency:\s*([\d.]+)\s*%'
    wasted_bytes_pattern = r'wastedBytes:\s*(\d+)\s*bytes'
    user_wasted_percent_pattern = r'userWastedPercent:\s*([\d.]+)\s*%'

    # Search for the patterns in the output
    efficiency_match = re.search(efficiency_pattern, output)
    wasted_bytes_match = re.search(wasted_bytes_pattern, output)
    user_wasted_percent_match = re.search(user_wasted_percent_pattern, output)

    # Extract the values and convert them to the appropriate types
    efficiency = float(efficiency_match.group(1)) if efficiency_match else None
    wasted_bytes = int(wasted_bytes_match.group(1)) if wasted_bytes_match else None
    user_wasted_percent = float(user_wasted_percent_match.group(1)) if user_wasted_percent_match else None

    return {
        'efficiency': efficiency,
        'wastedBytes': wasted_bytes,
        'userWastedPercent': user_wasted_percent,
    }
