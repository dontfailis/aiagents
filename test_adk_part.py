import sys
sys.path.append(".venv/lib/python3.11/site-packages")
try:
    from google.adk.events import UserMessagePart
    part = UserMessagePart(text="hello")
    print(getattr(part, "kind", None))
except Exception as e:
    print(e)
