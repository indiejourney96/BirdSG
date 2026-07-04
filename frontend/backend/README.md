# BirdSG Auth Backend

This folder contains the server-side authentication layer used by the Next.js app.

## Environment variables

Create `frontend/.env.local` with:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
AUTH_SESSION_SECRET=generate_a_long_random_secret_at_least_32_chars
NEXT_PUBLIC_APP_BASE_URL=http://localhost:3000
```

Use a different `NEXT_PUBLIC_APP_BASE_URL` in production, for example your HTTPS domain.

## Supabase schema

Run [`schema.sql`](./auth/schema.sql) in the Supabase SQL editor.

## What is included

- Email/password login
- CSRF protection for auth POST requests
- Secure httpOnly session cookies
- Session persistence with remember-me support
- Logout
- Password reset request and reset confirmation endpoints
- Login throttling: 5 failed attempts per 15 minutes
- Security event logging

## Password reset flow

1. `POST /api/auth/password-reset/request` with an email address
2. In development, the API returns a reset URL for convenience
3. `POST /api/auth/password-reset/confirm` with the token and new password

## Notes

- The app uses Supabase as the database and service-role access layer.
- Passwords are hashed with bcrypt salt rounds 12.
- The login form uses generic error messages so the API does not reveal whether an email exists.
