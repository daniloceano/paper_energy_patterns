# Como fazer o deploy do site — Guia Completo

Este guia ensina passo a passo como publicar o site **Energy Patterns** na Vercel, do zero. Não é necessário experiência prévia com deploy.

> **TL;DR para quem já conhece o fluxo:**
> 1. Crie bucket `figures` público no Supabase Storage
> 2. Rode `python scripts/web/upload_figures_to_supabase.py`
> 3. Configure `Root Directory = web` na Vercel
> 4. Adicione `NEXT_PUBLIC_SUPABASE_FIGURES_URL` nas env vars da Vercel
> 5. Push → deploy automático

---

## Por que as figuras não ficam no Git?

As figuras são geradas pelo pipeline científico (scripts Python) e pesam ~100 MB. Colocar binários gerados no Git é uma má prática — o repositório fica pesado e difícil de gerenciar.

A solução adotada:
- **Figuras** → ficam no **Supabase Storage** (CDN gratuito, acesso por URL pública)
- **Código e metadados** → ficam no Git
- **Vercel** → faz o build do site e referencia as figuras pelo URL do Supabase

---

## Pré-requisitos

- Conta no [GitHub](https://github.com) com o repositório já criado
- Acesso ao terminal (macOS/Linux) ou WSL (Windows)
- Python 3.9+ com o pipeline científico rodando

---

## Passo 1 — Criar uma conta e projeto no Supabase

O Supabase é onde as figuras vão ficar hospedadas. A conta gratuita é suficiente.

### 1.1 Criar conta

1. Acesse [supabase.com](https://supabase.com) e clique em **Start your project**.
2. Faça login com sua conta do GitHub.

### 1.2 Criar um projeto novo

1. Na tela inicial do Supabase, clique em **New project**.
2. Preencha:
   - **Organization**: selecione ou crie uma organização (pode ser o seu nome).
   - **Name**: `paper-energy-patterns` (ou qualquer nome que preferir).
   - **Database Password**: crie uma senha forte e **guarde** — você vai precisar dela.
   - **Region**: escolha a região mais próxima de você (ex.: `South America (São Paulo)`).
3. Clique em **Create new project**.
4. Aguarde 1–2 minutos até o projeto estar pronto (barra de progresso no topo).

---

## Passo 2 — Criar o bucket de figuras no Supabase Storage

O Supabase Storage é como um Google Drive para arquivos do site.

### 2.1 Acessar o Storage

No painel do seu projeto Supabase:
1. Clique em **Storage** no menu lateral esquerdo.
2. Clique em **New bucket**.

### 2.2 Configurar o bucket

Preencha:
- **Name**: `figures`
- **Public bucket**: ✅ marque esta opção (para que as imagens sejam acessíveis publicamente)

Clique em **Save**.

> ⚠️ Se esquecer de marcar "Public", as imagens não vão aparecer no site. Se isso acontecer, clique no bucket → **Edit** → marque "Public" → salve.

### 2.3 Verificar o acesso público

Para confirmar que funcionou, anote a URL base do seu projeto. Ela fica em:

**Settings** (ícone de engrenagem) → **API** → campo **Project URL**

A URL tem o formato: `https://xxxxxxxxxxxxxxxx.supabase.co`

Anote essa URL — você vai precisar dela.

---

## Passo 3 — Obter as credenciais do Supabase

Você vai precisar de duas chaves:

1. Vá em **Settings** → **API**.
2. Anote os valores de:
   - **Project URL** → ex.: `https://abcdefgh12345678.supabase.co`
   - **anon / public** (em "Project API keys") → chave pública, segura de expor
   - **service_role** (em "Project API keys") → ⚠️ **secreta**, nunca commitar

> **Atenção:** A chave `service_role` tem acesso total ao seu banco. Use-a **apenas localmente** para o upload das figuras. Nunca coloque no código ou no Git.

---

## Passo 4 — Fazer upload das figuras para o Supabase

Este passo é feito **na sua máquina**, depois de rodar o pipeline científico.

### 4.1 Instalar dependências

```bash
pip install supabase
```

### 4.2 Exportar as credenciais no terminal

No macOS/Linux, execute no terminal (substitua pelos seus valores reais):

```bash
export SUPABASE_URL=https://xxxxxxxxxxxxxxxx.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=eyJ...SUA_SERVICE_ROLE_KEY...
```

> Essas variáveis existem apenas na sessão atual do terminal — fechar o terminal as apaga. Isso é intencional por segurança.

### 4.3 Verificar o que será enviado (simulação)

```bash
python scripts/web/upload_figures_to_supabase.py --dry-run
```

Isso mostra quais arquivos seriam enviados sem realmente enviá-los.

### 4.4 Enviar as figuras

```bash
# Primeiro envio
python scripts/web/upload_figures_to_supabase.py

# Após atualizar as figuras (sobrescrever existentes)
python scripts/web/upload_figures_to_supabase.py --overwrite
```

O script exibirá algo como:
```
✓  cluster/pca_variance_wide.png
✓  cluster/pca_loadings_wide.png
✓  ep_structure/composite_egr.png
...
✓ Uploaded : 18
– Skipped  : 0
✗ Errors   : 0

SET THIS ENV VAR IN VERCEL:
  NEXT_PUBLIC_SUPABASE_FIGURES_URL = https://xxxxxxxx.supabase.co/storage/v1/object/public/figures
```

**Copie esse valor** — você vai configurá-lo na Vercel logo adiante.

### 4.5 Verificar se o upload funcionou

Abra essa URL no navegador (substitua pelo seu projeto e um arquivo que você acabou de enviar):

```
https://xxxxxxxxxxxxxxxx.supabase.co/storage/v1/object/public/figures/cluster/pca_variance_wide.png
```

Se abrir uma imagem: ✅ tudo certo.
Se aparecer erro: veja a seção de diagnóstico no final deste guia.

---

## Passo 5 — Criar conta e importar o projeto na Vercel

A Vercel hospeda o site Next.js e faz deploy automático a cada push.

### 5.1 Criar conta na Vercel

1. Acesse [vercel.com](https://vercel.com) e clique em **Sign Up**.
2. Escolha **Continue with GitHub** e autorize o acesso.

### 5.2 Importar o repositório

1. Na tela inicial da Vercel, clique em **Add New...** → **Project**.
2. Encontre o repositório `paper_energy_patterns` na lista.
3. Clique em **Import**.

---

## Passo 6 — Configurar o projeto na Vercel

### 6.1 Configurar o Root Directory ⚠️ (passo crítico)

O site Next.js está na pasta `web/`, não na raiz do repositório. Você precisa informar isso à Vercel.

Na tela de configuração do projeto:

1. Encontre o campo **Root Directory**.
2. Clique no ícone de lápis ✏️ ao lado dele.
3. Digite: `web`
4. Clique em **Save** ou confirme.

Se não fizer isso, a Vercel vai tentar fazer o build na raiz do repositório e vai falhar.

### 6.2 Configurar as variáveis de ambiente

Na mesma tela, procure a seção **Environment Variables** e adicione:

| Nome | Valor | Para que serve |
|------|-------|---------------|
| `NEXT_PUBLIC_SUPABASE_FIGURES_URL` | `https://xxxxxxxx.supabase.co/storage/v1/object/public/figures` | URL das figuras (obrigatório para imagens aparecerem) |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxxxxx.supabase.co` | URL do projeto Supabase (opcional por enquanto) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Chave anon pública do Supabase (opcional por enquanto) |

> O valor de `NEXT_PUBLIC_SUPABASE_FIGURES_URL` é o que o script de upload mostrou no final — format: `https://<seu-projeto>.supabase.co/storage/v1/object/public/figures`

Para adicionar cada variável:
1. Digite o nome no campo **Key**.
2. Cole o valor no campo **Value**.
3. Deixe marcado para todos os ambientes (Production, Preview, Development).
4. Clique em **Add**.

### 6.3 Fazer o deploy

Clique em **Deploy**. A Vercel vai:
1. Clonar o repositório.
2. Entrar na pasta `web/`.
3. Rodar `npm install`.
4. Rodar `npm run build` (gera o site estático).
5. Publicar o site.

O processo leva cerca de 2–3 minutos.

---

## Passo 7 — Verificar se funcionou

Depois do deploy:

1. Clique em **Visit** para abrir o site.
2. Navegue até **Analyses** → **Cluster Analysis** → **Step 2 — PCA**.
3. As figuras de PCA devem aparecer. ✅
4. Navegue até **Analyses** → **Composites** → **EGR**.
5. O mapa compósito deve aparecer (se `step4_create_figures.py` já foi rodado e as figuras foram enviadas ao Supabase). ✅

---

## Como funciona o deploy automático

Depois da configuração inicial, **você não precisa fazer mais nada manual**. A cada vez que você fizer `git push`, a Vercel detecta a mudança e redeploy automaticamente:

```bash
# Editou alguma coisa no site ou scripts
git add .
git commit -m "Atualiza página de análise"
git push
# → Vercel faz o deploy automaticamente em ~2 minutos
```

> **Figuras não precisam de redeploy!** Quando você reprocessa as figuras e faz upload para o Supabase (`--overwrite`), elas ficam disponíveis imediatamente no site sem precisar de redeploy.

---

## Fluxo completo — do pipeline científico ao site

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Pipeline científica (sua máquina)                        │
│    python scripts/ep_structure_analysis/step4_create_figures.py  │
│    python scripts/ep_structure_analysis/step5_update_scientific_notes.py │
│    → gera: figures/cluster/*.png, figures/ep_structure/*.png │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Manifests web (sua máquina)                              │
│    python scripts/web/build_site_manifest.py                │
│    python scripts/web/extract_composite_site_data.py        │
│    → gera: web/src/content/*.json                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Upload figuras para Supabase (sua máquina)               │
│    python scripts/web/upload_figures_to_supabase.py         │
│    → figuras disponíveis em: supabase.co/.../figures/*      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Commit apenas os manifests (sem figuras)                 │
│    git add web/src/content/                                 │
│    git add results/ep_structure/composite_stats.json        │
│    git commit -m "Atualiza manifests"                       │
│    git push → Vercel faz redeploy automático                │
└─────────────────────────────────────────────────────────────┘
```

---

## O que commitar e o que NÃO commitar

### ✅ Commitar (devem estar no Git)

| Arquivo | Por quê |
|---------|---------|
| `web/src/content/*.json` | Manifests lidos pelo site em build time |
| `results/ep_structure/composite_stats.json` | Estatísticas geradas pelo step5 |
| `scripts/web/*.py` | Scripts de extração e upload |
| `web/**/*.ts`, `web/**/*.tsx` | Código do site |
| `web/.env.example` | Documenta as variáveis necessárias |
| `web/DEPLOYMENT.md` | Este guia |

### ❌ NÃO commitar (esses já estão no `.gitignore`)

| Arquivo | Por quê |
|---------|---------|
| `figures/**/*.png` | Servidos pelo Supabase Storage |
| `figures/**/*.svg` | Servidos pelo Supabase Storage |
| `data/**/*.nc` | Arquivos ERA5 pesados (~GBs) |
| `web/.env.local` | Contém segredos — só na sua máquina |
| `web/node_modules/` | Instalado pela Vercel automaticamente |
| `web/.next/` | Gerado pela Vercel automaticamente |

> **Como verificar?** Rode `git status` antes de commitar. Se aparecer algum `.png` ou `.nc`, algo está errado com o `.gitignore`.

---

## Desenvolvimento local (sem Supabase)

Para rodar o site na sua máquina sem precisar de conta no Supabase:

```bash
cd web
npm install
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000).

As figuras são servidas automaticamente do disco local (`figures/`) via a rota `/api/figures`. Você **não precisa** configurar Supabase nem fazer upload — desde que as figuras existam na pasta `figures/`.

---

## Diagnóstico — o que fazer se algo der errado

### Figuras não aparecem no site (ícone quebrado ?)

**Passo 1:** Verifique se a env var está configurada na Vercel:
- Vercel → seu projeto → Settings → Environment Variables
- Deve existir `NEXT_PUBLIC_SUPABASE_FIGURES_URL`

**Passo 2:** Verifique se a URL do Supabase funciona:
```
https://<seu-projeto>.supabase.co/storage/v1/object/public/figures/cluster/pca_variance_wide.png
```
- Abre imagem → ✅ URL correta, bucket público
- Erro 404 → Arquivo não foi enviado. Rode: `python scripts/web/upload_figures_to_supabase.py`
- Erro 400/401 → Bucket não é público. Vá ao Supabase Storage → bucket `figures` → Edit → marque Public

**Passo 3:** Veja os logs na Vercel:
- Vercel → Deployments → clique no deploy → Build Logs
- Procure por erros em vermelho

### Build falhou na Vercel

- Verifique se **Root Directory = `web`** está configurado
- Verifique se `web/src/content/*.json` estão commitados (rode `git ls-files web/src/content/`)
- Rode `npm run build` localmente para ver o erro exato

### "Cannot find module" ou erro de TypeScript

```bash
cd web
npm install
npm run typecheck
npm run build
```

Se falhar localmente, vai falhar na Vercel também. Corrija antes de fazer push.

---

## Como fazer redeploy manualmente

```bash
# Opção 1: push de commit vazio
git commit --allow-empty -m "redeploy"
git push

# Opção 2: pelo painel
# Vercel → Deployments → ⋯ → Redeploy
```

---

## Referência rápida de variáveis de ambiente

| Variável | Onde usar | Obrigatória? | Onde pegar |
|----------|-----------|-------------|-----------|
| `NEXT_PUBLIC_SUPABASE_FIGURES_URL` | Vercel | ✅ Sim | Saída do upload script |
| `NEXT_PUBLIC_SUPABASE_URL` | Vercel | Não (por enquanto) | Supabase → Settings → API → Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Vercel | Não (por enquanto) | Supabase → Settings → API → anon/public key |
| `SUPABASE_URL` | Só local (terminal) | Para upload | Supabase → Settings → API → Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Só local (terminal) | Para upload | Supabase → Settings → API → service_role key ⚠️ |

> ⚠️ `SUPABASE_SERVICE_ROLE_KEY` nunca deve ir para o Git nem para a Vercel — use apenas localmente para o upload.
