# Backend Email

Jarvis renders transactional email from MJML/fallback templates under `backend/src/templates/email/`.

## Active Templates

- `verification`: confirm a new account email.
- `welcome`: first verified account welcome.
- `reset_password`: password reset.
- `account_deletion`: account deletion confirmation.
- `newsletter_welcome`: optional product updates.

Runtime rendering uses `render_email_template` and logs send attempts to `email_log`.

## Notes

Compiled templates are intentionally not kept in this cleaned baseline. Rebuild them locally if the deployment path requires precompiled HTML.
