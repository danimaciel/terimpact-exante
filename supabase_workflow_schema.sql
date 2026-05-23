-- TerImpact workflow schema
-- Execute este arquivo no SQL Editor do Supabase depois de criar o projeto.
-- Ele cria a estrutura para login, perfis, propostas, avaliacao e tramitacao.

create extension if not exists pgcrypto;

do $$
begin
    create type public.user_role as enum ('proponente', 'cti', 'tt', 'admin');
exception
    when duplicate_object then null;
end $$;

do $$
begin
    create type public.proposta_status as enum (
        'rascunho',
        'enviada_cti',
        'em_analise_cti',
        'ajuste_solicitado',
        'encaminhada_tt',
        'em_trabalho_tt',
        'devolvida_cti',
        'finalizada',
        'arquivada'
    );
exception
    when duplicate_object then null;
end $$;

do $$
begin
    create type public.workflow_stage as enum ('proponente', 'cti', 'tt');
exception
    when duplicate_object then null;
end $$;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null unique,
    nome text,
    papel public.user_role not null default 'proponente',
    unidade text,
    ativo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.propostas (
    id uuid primary key default gen_random_uuid(),
    codigo text not null unique,
    created_by uuid references auth.users(id),
    titulo text not null,
    proponente_nome text,
    proponente_email text,
    equipe jsonb not null default '[]'::jsonb,
    unidade text,
    area_tematica text,
    portfolio text,
    tipo_proposta text,
    duracao_meses integer,
    valor_solicitado numeric,
    parceiros jsonb not null default '[]'::jsonb,
    publicos_alvo jsonb not null default '[]'::jsonb,
    resumo text,
    anotacoes_proponente text,
    consideracoes text,
    status public.proposta_status not null default 'rascunho',
    current_owner_role public.user_role not null default 'proponente',
    submitted_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.proposta_resultados (
    id uuid primary key default gen_random_uuid(),
    proposta_id uuid not null references public.propostas(id) on delete cascade,
    id_resultado text,
    categoria_resultado text,
    tipo_resultado text not null,
    comprovante_resultado text,
    exemplos_resultado text,
    detalhamento text,
    created_at timestamptz not null default now(),
    unique (proposta_id, tipo_resultado)
);

alter table public.proposta_resultados
    add column if not exists detalhamento text;

create table if not exists public.respostas_indicadores (
    id uuid primary key default gen_random_uuid(),
    proposta_id uuid not null references public.propostas(id) on delete cascade,
    etapa public.workflow_stage not null,
    codigo text not null,
    dimensao text not null,
    pergunta text not null,
    nota integer check (nota between 1 and 5),
    descricao_resposta text,
    anotacao text,
    created_by uuid references auth.users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (proposta_id, etapa, codigo)
);

create table if not exists public.indices_avaliacao (
    id uuid primary key default gen_random_uuid(),
    proposta_id uuid not null references public.propostas(id) on delete cascade,
    etapa public.workflow_stage not null,
    impacto_potencial numeric,
    maturidade_trajetoria numeric,
    capacidade_institucional numeric,
    indice_estrategico numeric,
    classificacao text,
    dimensoes jsonb not null default '{}'::jsonb,
    calculated_by uuid references auth.users(id),
    calculated_at timestamptz not null default now(),
    unique (proposta_id, etapa)
);

create table if not exists public.tramitacoes (
    id uuid primary key default gen_random_uuid(),
    proposta_id uuid not null references public.propostas(id) on delete cascade,
    from_status public.proposta_status,
    to_status public.proposta_status not null,
    from_role public.user_role,
    to_role public.user_role,
    actor_id uuid references auth.users(id),
    comentario text,
    created_at timestamptz not null default now()
);

create table if not exists public.comentarios (
    id uuid primary key default gen_random_uuid(),
    proposta_id uuid not null references public.propostas(id) on delete cascade,
    actor_id uuid references auth.users(id),
    papel public.user_role,
    comentario text not null,
    privado boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists profiles_papel_idx
    on public.profiles (papel);

create index if not exists propostas_status_idx
    on public.propostas (status);

create index if not exists propostas_created_by_idx
    on public.propostas (created_by);

create index if not exists propostas_current_owner_role_idx
    on public.propostas (current_owner_role);

create index if not exists respostas_indicadores_proposta_idx
    on public.respostas_indicadores (proposta_id);

create index if not exists tramitacoes_proposta_idx
    on public.tramitacoes (proposta_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists set_profiles_updated_at on public.profiles;
create trigger set_profiles_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

drop trigger if exists set_propostas_updated_at on public.propostas;
create trigger set_propostas_updated_at
before update on public.propostas
for each row execute function public.set_updated_at();

drop trigger if exists set_respostas_indicadores_updated_at on public.respostas_indicadores;
create trigger set_respostas_indicadores_updated_at
before update on public.respostas_indicadores
for each row execute function public.set_updated_at();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, email, nome, papel)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data->>'nome', new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
        coalesce((new.raw_user_meta_data->>'papel')::public.user_role, 'proponente'::public.user_role)
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

alter table public.profiles enable row level security;
alter table public.propostas enable row level security;
alter table public.proposta_resultados enable row level security;
alter table public.respostas_indicadores enable row level security;
alter table public.indices_avaliacao enable row level security;
alter table public.tramitacoes enable row level security;
alter table public.comentarios enable row level security;

create or replace function public.current_user_role()
returns public.user_role
language sql
stable
security definer
set search_path = public
as $$
    select papel from public.profiles where id = auth.uid() and ativo = true
$$;

drop policy if exists "profiles_select_own_or_admin" on public.profiles;
create policy "profiles_select_own_or_admin"
on public.profiles
for select
to authenticated
using (
    id = auth.uid()
    or public.current_user_role() = 'admin'
);

drop policy if exists "profiles_update_own_basic" on public.profiles;
create policy "profiles_update_own_basic"
on public.profiles
for update
to authenticated
using (id = auth.uid())
with check (id = auth.uid());

drop policy if exists "propostas_insert_authenticated" on public.propostas;
create policy "propostas_insert_authenticated"
on public.propostas
for insert
to authenticated
with check (created_by = auth.uid());

drop policy if exists "propostas_select_by_role" on public.propostas;
create policy "propostas_select_by_role"
on public.propostas
for select
to authenticated
using (
    created_by = auth.uid()
    or public.current_user_role() in ('admin', 'cti')
    or (
        public.current_user_role() = 'tt'
        and status in ('encaminhada_tt', 'em_trabalho_tt', 'devolvida_cti', 'finalizada')
    )
);

drop policy if exists "propostas_update_by_role" on public.propostas;
create policy "propostas_update_by_role"
on public.propostas
for update
to authenticated
using (
    created_by = auth.uid()
    or public.current_user_role() in ('admin', 'cti', 'tt')
)
with check (
    created_by = auth.uid()
    or public.current_user_role() in ('admin', 'cti', 'tt')
);

drop policy if exists "proposta_resultados_manage_by_proposta_access" on public.proposta_resultados;
create policy "proposta_resultados_manage_by_proposta_access"
on public.proposta_resultados
for all
to authenticated
using (
    exists (
        select 1
        from public.propostas p
        where p.id = proposta_id
        and (
            p.created_by = auth.uid()
            or public.current_user_role() in ('admin', 'cti', 'tt')
        )
    )
)
with check (
    exists (
        select 1
        from public.propostas p
        where p.id = proposta_id
        and (
            p.created_by = auth.uid()
            or public.current_user_role() in ('admin', 'cti', 'tt')
        )
    )
);

drop policy if exists "respostas_manage_by_role" on public.respostas_indicadores;
create policy "respostas_manage_by_role"
on public.respostas_indicadores
for all
to authenticated
using (
    public.current_user_role() in ('admin', 'cti', 'tt')
    or created_by = auth.uid()
)
with check (
    public.current_user_role() in ('admin', 'cti', 'tt')
    or created_by = auth.uid()
);

drop policy if exists "indices_manage_by_role" on public.indices_avaliacao;
create policy "indices_manage_by_role"
on public.indices_avaliacao
for all
to authenticated
using (
    public.current_user_role() in ('admin', 'cti', 'tt')
    or calculated_by = auth.uid()
)
with check (
    public.current_user_role() in ('admin', 'cti', 'tt')
    or calculated_by = auth.uid()
);

drop policy if exists "tramitacoes_select_by_proposta_access" on public.tramitacoes;
create policy "tramitacoes_select_by_proposta_access"
on public.tramitacoes
for select
to authenticated
using (
    exists (
        select 1
        from public.propostas p
        where p.id = proposta_id
        and (
            p.created_by = auth.uid()
            or public.current_user_role() in ('admin', 'cti', 'tt')
        )
    )
);

drop policy if exists "tramitacoes_insert_by_role" on public.tramitacoes;
create policy "tramitacoes_insert_by_role"
on public.tramitacoes
for insert
to authenticated
with check (public.current_user_role() in ('admin', 'cti', 'tt', 'proponente'));

drop policy if exists "comentarios_manage_by_proposta_access" on public.comentarios;
create policy "comentarios_manage_by_proposta_access"
on public.comentarios
for all
to authenticated
using (
    actor_id = auth.uid()
    or public.current_user_role() in ('admin', 'cti', 'tt')
)
with check (
    actor_id = auth.uid()
    or public.current_user_role() in ('admin', 'cti', 'tt')
);
