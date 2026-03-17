# Como fazer o deploy do site — Guia Completo

Este guia ensina passo a passo como publicar o site **Energy Patterns** na Vercel, do zero. Não é necessário experiência prévia com deploy.

> **TL;DR para quem já conhece o fluxo:**
> 1. `python scripts/web/copy_figures_to_web.py`
> 2. `git add web/public/figures/ && git commit -m "Update figures" && git push`
> 3. Configure `Root Directory = web` na Vercel
> 4. Push → deploy automático

---

## Como as figuras funcionam no site

As figuras são servidas como **assets estáticos do Next.js** a partir de `web/public/figures/`. Elas ficam no Git como parte do site (não como output científico).

| Diretório | O que fica ali | No Git? |
|---|---|---|
| `figures/` | Output do pipeline científico (PNG brutos) | ❌ Gitignored |
| `web/public/figures/` | Cópia das figuras usadas pelo site | ✅ Commitado |

Quando as figuras científicas são regeneradas, você roda um script que copia apenas as necessárias para `web/public/figures/` e faz um commit.

Fluxos suportados para as figuras
--------------------------------

1) Static (padrão): copie as figuras necessárias para `web/public/figures/`, commit e push. A Vercel servirá os assets em `/figures/...` automaticamente.

2) Supabase (opcional): faça upload das figuras para o bucket público `figures` no Supabase e defina a variável `NEXT_PUBLIC_SUPABASE_FIGURES_URL` no painel da Vercel apontando para `https://<project>.supabase.co/storage/v1/object/public/figures`. **ATENÇÃO:** o upload para o Supabase não é feito por `git push` — é necessário executar `python scripts/web/upload_figures_to_supabase.py` explicitamente. O script também sugere o valor exato de `NEXT_PUBLIC_SUPABASE_FIGURES_URL` a ser configurado.


**Supabase Storage** pode ser usado como alternativa (CDN externo), mas não é obrigatório. O site funciona sem ele.

---
- **Vercel** → faz o build do site e referencia as figuras pelo URL do Supabase (se configurado). Importante: um `git push` NÃO envia figuras para o Supabase — é necessário executar o script de upload explicitamente.

---

## Pré-requisitos

- Conta no [GitHub](https://github.com) com o repositório já criado
- Acesso ao terminal (macOS/Linux) ou WSL (Windows)
- Python 3.9+ instalado (para o script de cópia das figuras)

---

## Passo 1 — Garantir que as figuras do site estão no repositório

As figuras do site vivem em `web/public/figures/`. Elas já foram adicionadas ao repositório, então o **deploy inicial não precisa de nenhum passo extra**.

Mas quando você **regenerar as figuras** do pipeline científico, precisará atualizar o site:

```bash
# Na raiz do repositório:

# 1. Regenere as figuras (pipeline científico)
python scripts/ep_structure_analysis/step4_create_figures.py
python scripts/cluster_analysis_energy_patterns/run_pipeline.py

# 2. Copie as figuras necessárias para o site
python scripts/web/copy_figures_to_web.py

# 3. Regenere os manifests
python scripts/web/extract_composite_site_data.py

# 4. Commit e push (Vercel vai fazer redeploy automático)
git add web/public/figures/
git add web/src/content/
git commit -m "Atualiza figuras e manifests do site"
git push
```

> **Por que commitar as figuras do site?** A pasta `web/public/figures/` contém apenas as ~36 figuras usadas pelo site (≈ 25 MB), não o output completo do pipeline. A pasta `figures/` (output científico) continua gitignored.

---

## Passo 1 (opcional) — Criar conta e projeto no Supabase

O Supabase é o banco de dados do site. Você **não precisa** do Supabase para ver as figuras — elas são servidas diretamente do repositório. O Supabase é usado para funcionalidades futuras de banco de dados.

Se quiser configurar:

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

## Passo 3 — Criar conta e importar o projeto na Vercel

A Vercel hospeda o site Next.js e faz deploy automático a cada push.

### 5.1 Criar conta na Vercel

1. Acesse [vercel.com](https://vercel.com) e clique em **Sign Up**.
2. Escolha **Continue with GitHub** e autorize o acesso.

### 5.2 Importar o repositório

1. Na tela inicial da Vercel, clique em **Add New...** → **Project**.
2. Encontre o repositório `paper_energy_patterns` na lista.
3. Clique em **Import**.

---

## Passo 4 — Configurar o projeto na Vercel

### 4.1 Configurar o Root Directory ⚠️ (passo crítico)

O site Next.js está na pasta `web/`, não na raiz do repositório. Você precisa informar isso à Vercel.

Na tela de configuração do projeto:

1. Encontre o campo **Root Directory**.
2. Clique no ícone de lápis ✏️ ao lado dele.
3. Digite: `web`
4. Clique em **Save** ou confirme.

Se não fizer isso, a Vercel vai tentar fazer o build na raiz do repositório e vai falhar.

### 4.2 Variáveis de ambiente (opcionais)

As figuras já estão no repositório, então **variáveis de ambiente não são obrigatórias** para o site funcionar. Mas se quiser usar Supabase (banco de dados), adicione:

| Nome | Valor | Para que serve |
|------|-------|---------------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxxxxx.supabase.co` | URL do projeto Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Chave anon pública do Supabase |
| `NEXT_PUBLIC_SUPABASE_FIGURES_URL` | `https://xxxxxxxx.supabase.co/storage/v1/object/public/figures` | Sobrescreve URL das figuras (opcional) |

Para adicionar cada variável:
1. Digite o nome no campo **Key**.
2. Cole o valor no campo **Value**.
3. Deixe marcado para todos os ambientes (Production, Preview, Development).
4. Clique em **Add**.

### 4.3 Fazer o deploy

Clique em **Deploy**. A Vercel vai:
1. Clonar o repositório.
2. Entrar na pasta `web/`.
3. Rodar `npm install`.
4. Rodar `npm run build` (gera o site estático com as figuras de `web/public/figures/`).
5. Publicar o site.

O processo leva cerca de 2–3 minutos.

---

## Passo 5 — Verificar se funcionou

Depois do deploy:

1. Clique em **Visit** para abrir o site.
2. Navegue até **Analyses** → **Cluster Analysis** → **Step 2 — PCA**.
3. As figuras de PCA devem aparecer. ✅
4. Navegue até **Analyses** → **Composites** → **EGR**.
5. O mapa compósito deve aparecer. ✅

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
│ 2. Copiar figuras para o site (sua máquina)                 │
│    python scripts/web/copy_figures_to_web.py                │
│    → copia: figures/ → web/public/figures/                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Manifests web (sua máquina)                              │
│    python scripts/web/extract_composite_site_data.py        │
│    → gera: web/src/content/*.json                           │
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Upload figuras para Supabase (sua máquina)               │
│    # Preview (dry-run):                                      │
│    python scripts/web/upload_figures_to_supabase.py --dry-run │
│    # Upload (writes to public bucket 'figures'):             │
│    python scripts/web/upload_figures_to_supabase.py         │
│    → After success the script prints the exact NEXT_PUBLIC_SUPABASE_FIGURES_URL value to set in Vercel. │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Commit figuras + manifests → push → deploy               │
│    git add web/public/figures/                              │
│    git add web/src/content/                                 │
│    git commit -m "Atualiza figuras e manifests"             │
│    git push → Vercel faz redeploy automático                │
└─────────────────────────────────────────────────────────────┘
```

---

## O que commitar e o que NÃO commitar

### ✅ Commitar (devem estar no Git)

| Arquivo | Por quê |
|---------|---------|
| `web/public/figures/` | Assets estáticos do site (servidos pelo Vercel) |
| `web/src/content/*.json` | Manifests lidos pelo site em build time |
| `results/ep_structure/composite_stats.json` | Estatísticas geradas pelo step5 |
| `scripts/web/*.py` | Scripts de extração e cópia |
| `web/**/*.ts`, `web/**/*.tsx` | Código do site |
| `web/.env.example` | Documenta as variáveis necessárias |
| `web/DEPLOYMENT.md` | Este guia |

### ❌ NÃO commitar (esses já estão no `.gitignore`)

| Arquivo | Por quê |
|---------|---------|
| `figures/**/*.png` | Output científico bruto (grande, gitignored) |
| `figures/**/*.svg` | Output científico bruto (gitignored) |
| `data/**/*.nc` | Arquivos ERA5 pesados (~GBs) |
| `web/.env.local` | Contém segredos — só na sua máquina |
| `web/node_modules/` | Instalado pela Vercel automaticamente |
| `web/.next/` | Gerado pela Vercel automaticamente |

> **Como verificar?** Rode `git status` antes de commitar. Arquivos em `figures/` (raiz) nunca devem aparecer — mas `web/public/figures/` é normal aparecer.

---

## Desenvolvimento local

Para rodar o site na sua máquina:

```bash
cd web
npm install
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000).

As figuras são servidas de `web/public/figures/` (que já estão commitadas). **Não precisa de Supabase nem de configuração extra.**

---

## Diagnóstico — o que fazer se algo der errado

### Figuras não aparecem no site (ícone quebrado ?)

**Passo 1:** Verifique se os arquivos estão commitados:
```bash
git ls-files web/public/figures/ | head -5
```
Se retornar vazio, rode `python scripts/web/copy_figures_to_web.py` e depois `git add web/public/figures/` + commit.

**Passo 2:** Verifique se a URL funciona depois do deploy:
```
https://seu-site.vercel.app/figures/cluster/pca_variance_wide.png
```
- Abre imagem → ✅ correto
- Erro 404 → arquivo não foi commitado

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

| Variável | Onde usar | Obrigatória? | Para que serve |
|----------|-----------|-------------|-----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Vercel | ❌ Não | URL do Supabase (banco de dados) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Vercel | ❌ Não | Chave pública do Supabase |
| `NEXT_PUBLIC_SUPABASE_FIGURES_URL` | Vercel | ❌ Não | Override URL das figuras para Supabase Storage |

> As figuras já são servidas via `web/public/figures/` (estático). Nenhuma variável de ambiente é obrigatória para o site funcionar.
