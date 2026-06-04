# Jarvis Backend

FastAPI backend for the Jarvis local-network home AI assistant.

## Setup

1. Create and activate a virtual environment.
2. Install Python dependencies from `requirements.txt`.
3. Copy `.env.template` to `.env` and fill in local database, mail, auth, and OAuth values.
4. Run migrations from the backend directory with the existing migration script.
5. Start the FastAPI application.

The repository agent instructions intentionally do not validate these steps from this sandbox. Run the commands locally when needed.

## Active Backend Areas

- Authentication and refresh-cookie sessions.
- Google sign-in and account linking.
- User profile, password reset, email verification, and account deletion.
- Admin user listing and account actions.
- Contact and newsletter submissions.
- Email rendering/logging, announcements, blocked-domain registration checks, and traffic log ingestion.

The Jarvis baseline removes the copied commerce, usage-metering, and image-workflow modules.
