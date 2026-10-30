-- The first migration. Add more as 002_....sql, 003_....sql: each runs once, in order, when the app
-- starts (std/migrate). Don't edit one that has run; add another that changes what it made.
create table users (
  id bigserial primary key,
  email text not null unique,
  password_hash text not null,
  created timestamptz not null default now()
);

create table notes (
  id bigserial primary key,
  user_id bigint not null references users on delete cascade,
  text text not null,
  created timestamptz not null default now()
);

create index notes_user on notes (user_id, id);
