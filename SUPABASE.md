# Configuração do Supabase

## 1. Criar o projeto

Crie um projeto no Supabase e guarde:

- Project URL
- API key `anon public` ou `service_role`

## 2. Criar a tabela

No Supabase, abra `SQL Editor` e execute o conteúdo de `supabase_schema.sql`.

## 3. Configurar o Streamlit Cloud

Em `App settings > Secrets`, adicione:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-chave-anon-ou-service-role"
SUPABASE_TABLE = "avaliacoes"
```

## 4. Comportamento do app

O app sempre salva uma cópia local em CSV. Quando as secrets acima estiverem configuradas, ele também salva cada avaliação na tabela `avaliacoes` do Supabase.

O campo `id_proposta` é gerado automaticamente pelo app no formato `TER-AAAAMMDD-XXXXXXXX`.
