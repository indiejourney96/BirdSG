alter table public.sightings
  add column if not exists user_id uuid;

alter table public.sightings
  drop constraint if exists sightings_user_id_fkey;

alter table public.sightings
  add constraint sightings_user_id_fkey
  foreign key (user_id)
  references public.users (id)
  on delete cascade;

create index if not exists sightings_user_id_created_at_idx
  on public.sightings using btree (user_id, created_at desc);

create index if not exists sightings_user_id_top_label_idx
  on public.sightings using btree (user_id, top_label);
