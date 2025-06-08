
create table if not exists price_history (
  id uuid default uuid_generate_v4() primary key,
  symbol text not null,
  price float8,
  timestamp timestamptz default now()
);

create table if not exists alerts_sent (
  id uuid default uuid_generate_v4() primary key,
  symbol text,
  alert_type text,
  details jsonb,
  timestamp timestamptz default now()
);

create table if not exists thresholds (
  id uuid default uuid_generate_v4() primary key,
  symbol text unique not null,
  thresholds jsonb not null,
  updated_at timestamptz default now()
);

create table if not exists event_logs (
  id uuid default uuid_generate_v4() primary key,
  timestamp timestamptz default now(),
  message text
);
