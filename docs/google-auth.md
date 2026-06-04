# Google Authentication

Jarvis uses Google Identity Services. It verifies user identity and does not request Google API access.

## Flow

1. The frontend loads `https://accounts.google.com/gsi/client`.
2. `GoogleSignInButton.vue` receives an ID token from Google.
3. The frontend posts that token to `POST /auth/google/login`.
4. The backend verifies the token with `google-auth`.
5. The backend creates or links a Jarvis user, returns an access token, and sets the refresh token as an `HttpOnly` cookie.

If an email already exists without a Google link, the backend returns `link_required`. The frontend prompts the user, then confirms with `POST /auth/google/link`.

## Environment

- Backend: `GOOGLE_OAUTH_CLIENT_ID`
- Frontend: `NUXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID` or `GOOGLE_OAUTH_CLIENT_ID`
- Optional: `SOCIAL_LINK_TOKEN_TTL_MINUTES`

Use a Web OAuth client id ending in `.apps.googleusercontent.com`. Do not use the client secret in frontend config.

## Files

- `backend/src/service/google_auth.py`
- `backend/src/routers/google_auth.py`
- `frontend/components/login/GoogleSignInButton.vue`
- `frontend/plugins/gis.client.ts`
- `frontend/nuxt.config.ts`
