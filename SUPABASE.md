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
ADMIN_PASSWORD = "uma-senha-forte-para-o-painel"
```

## 4. Comportamento do app

O app sempre salva uma cópia local em CSV. Quando as secrets acima estiverem configuradas, ele também salva cada avaliação na tabela `avaliacoes` do Supabase.

O campo `id_proposta` é gerado automaticamente pelo app no formato `TER-AAAAMMDD-XXXXXXXX`.

## 5. Painel de governança

O botão `Governança` abre uma área administrativa no app. O acesso exige a senha definida em `ADMIN_PASSWORD`.

No painel, é possível:

- consultar avaliações salvas no Supabase;
- buscar por título, proponente, unidade, área, portfólio ou ID;
- baixar os dados filtrados em CSV ou Excel.

## 6. Próxima arquitetura com login e tramitação

O arquivo `supabase_workflow_schema.sql` prepara o banco para o TerImpact como sistema com perfis e fluxo de trabalho.

Ele cria:

- `profiles`: perfis dos usuários autenticados, com papéis `proponente`, `cti`, `tt` e `admin`;
- `propostas`: cadastro principal das propostas e status da tramitação;
- `proposta_resultados`: resultados esperados vinculados a cada proposta;
- `respostas_indicadores`: notas e anotações dos indicadores;
- `indices_avaliacao`: índices calculados por etapa;
- `tramitacoes`: histórico de envio, análise, devolução e encaminhamento;
- `comentarios`: comentários associados às propostas.

Estados previstos para uma proposta:

- `rascunho`
- `enviada_cti`
- `em_analise_cti`
- `ajuste_solicitado`
- `encaminhada_tt`
- `em_trabalho_tt`
- `devolvida_cti`
- `finalizada`
- `arquivada`

Essa estrutura deve ser aplicada antes de migrar o app para login com Supabase Auth. A tabela simples `avaliacoes` continua existindo para compatibilidade com a versão atual.
