-- Run this in the Supabase SQL editor (Project → SQL Editor → New query)

create table if not exists reservations (
  id            bigint generated always as identity primary key,
  full_name     text not null,
  email         text not null,
  phone         text not null,
  account_number text,
  unit          text,
  price         numeric,
  status        text not null default 'pending_payment',
  created_at    timestamptz not null default now()
);

-- Row Level Security: the Flask backend talks to Supabase with the
-- service_role key (server-side only), which bypasses RLS. Enabling RLS
-- here just makes sure no anon/browser key could ever read or write this
-- table directly, even by mistake.
alter table reservations enable row level security;

-- No policies are created on purpose — that means zero access via the
-- anon/public key. Only the service_role key (used by app.py) can touch it.