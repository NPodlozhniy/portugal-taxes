import time
import sys

max_attempts = 10
delay = 3

for attempt in range(max_attempts):
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
        print("Database initialized successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Attempt {attempt + 1}/{max_attempts} failed: {e}")
        if attempt < max_attempts - 1:
            time.sleep(delay)

print("Failed to initialize database after all attempts")
sys.exit(1)
