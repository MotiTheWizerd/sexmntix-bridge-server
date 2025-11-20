from src.api.app import create_app
from fastapi.routing import APIRoute

app = create_app()

print("Registered Routes:")
found = False
for route in app.routes:
    if isinstance(route, APIRoute):
        if "user-projects" in route.path:
            print(f"- {route.path} [{','.join(route.methods)}]")
            found = True

if found:
    print("\nSUCCESS: user-projects routes found.")
else:
    print("\nFAILURE: user-projects routes NOT found.")
