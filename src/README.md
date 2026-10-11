# Mergington High School Activities API

A FastAPI application for browsing extracurricular activities. Activity and participant lists are public; only authenticated teachers can register or unregister students.

## Features

- View all available extracurricular activities
- Publicly view activities and their participant lists
- Teacher login for registering and unregistering students
- Capacity-aware activity listings

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Provision teacher credentials in `src/teachers.json`. Store a PBKDF2 hash rather than a plaintext password. Generate a hash with:

   ```sh
   python -c 'import base64, getpass, hashlib, secrets; p=getpass.getpass(); s=base64.urlsafe_b64encode(secrets.token_bytes(16)).decode().rstrip("="); d=hashlib.pbkdf2_hmac("sha256", p.encode(), base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)), 310000); print("pbkdf2_sha256$310000$" + s + "$" + base64.urlsafe_b64encode(d).decode().rstrip("="))'
   ```

   Add one entry per teacher to the `teachers` array, using the generated value as `password_hash`:

   ```json
   {
     "teachers": [
       {"username": "teacher1", "password_hash": "pbkdf2_sha256$310000$..."}
     ]
   }
   ```

   Set a stable signing secret before starting the app. For production, also enable secure cookies and serve over HTTPS:

   ```sh
   export ADMIN_SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   export COOKIE_SECURE=true
   ```

3. Run the application:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| GET    | `/auth/session`                                                   | Check whether the current browser has a teacher session              |
| POST   | `/auth/login`                                                      | Sign in with a configured teacher username and password              |
| POST   | `/auth/logout`                                                     | Sign out and clear the teacher session                               |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher session required)                        |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher session required)                    |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and participant data is stored in memory, which means it resets when the server restarts. Teacher credentials are read from `src/teachers.json`; do not store plaintext passwords there. Set `ADMIN_SESSION_SECRET` to a stable random value so teacher sessions can be verified across application restarts. Set `COOKIE_SECURE=true` when serving over HTTPS.

Run the API tests with `pip install -r requirements-dev.txt` followed by `pytest`.
