import re

def extract_task_id(url):
    youtube_regex = r"(?:v=|\/|embed\/|shorts\/|youtu\.be\/)([0-9A-Za-z_-]{11})(?:[?&]|$)"
    if "youtube.com" in url or "youtu.be" in url:
        id_match = re.search(youtube_regex, url)
        if id_match:
            return id_match.group(1)
    elif len(url) == 11 and re.match(r"^[0-9A-Za-z_-]{11}$", url):
        return url
    return None

test_cases = [
    ("https://www.youtube.com/watch?v=NRDWBQWiYeg", "NRDWBQWiYeg"),
    ("https://youtu.be/NRDWBQWiYeg", "NRDWBQWiYeg"),
    ("https://www.youtube.com/shorts/NRDWBQWiYeg", "NRDWBQWiYeg"),
    ("https://read-tube.com/result/NRDWBQWiYeg", None),
    ("NRDWBQWiYeg", "NRDWBQWiYeg"),
    ("https://example.com/something", None),
]

for url, expected in test_cases:
    result = extract_task_id(url)
    print(f"URL: {url:<50} | Expected: {str(expected):<15} | Result: {str(result):<15} | {'PASS' if result == expected else 'FAIL'}")
