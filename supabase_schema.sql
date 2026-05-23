create table if not exists public.avaliacoes (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    id_proposta text not null unique,
    titulo text,
    proponente text,
    cadastro jsonb not null,
    scores jsonb not null,
    anotacoes_indicadores jsonb not null,
    dim_scores jsonb not null,
    indices jsonb not null
);

create index if not exists avaliacoes_id_proposta_idx
    on public.avaliacoes (id_proposta);

create index if not exists avaliacoes_created_at_idx
    on public.avaliacoes (created_at desc);
