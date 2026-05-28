create extension if not exists pgcrypto;
create extension if not exists citext;

create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email citext not null unique,
  password_hash text not null,
  created_at timestamptz not null default now(),
  last_login timestamptz null,
  is_active boolean not null default true,
  email_verified_at timestamptz null
);

create table if not exists public.password_reset_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  token_hash text not null unique,
  expires_at timestamptz not null,
  used_at timestamptz null,
  created_at timestamptz not null default now()
);

create table if not exists public.auth_login_attempts (
  id uuid primary key default gen_random_uuid(),
  rate_limit_key text not null,
  email text not null,
  ip_address text not null,
  success boolean not null default false,
  reason text not null,
  attempted_at timestamptz not null default now()
);

create index if not exists auth_login_attempts_rate_limit_key_idx
  on public.auth_login_attempts (rate_limit_key, attempted_at desc);

create index if not exists auth_login_attempts_email_idx
  on public.auth_login_attempts (email, attempted_at desc);

create table if not exists public.auth_security_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists auth_security_events_event_type_idx
  on public.auth_security_events (event_type, created_at desc);

create index if not exists password_reset_tokens_user_id_idx
  on public.password_reset_tokens (user_id, created_at desc);

create index if not exists password_reset_tokens_token_hash_idx
  on public.password_reset_tokens (token_hash);
