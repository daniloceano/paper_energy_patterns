# Guia Operacional de Deploy — Energy Patterns

Este guia documenta o fluxo completo de publicação do site, desde gerar as figuras até o deploy na Vercel. É destinado a qualquer pessoa que precise atualizar o projeto, mesmo sem lembrar os detalhes de uma sessão anterior.

> **⚠️ CRITICAL DEPLOYMENT ORDER:**
> 1. ✅ Upload figures to Supabase **FIRST**
> 2. ✅ Set `NEXT_PUBLIC_SUPABASE_FIGURES_URL` in Vercel **SECOND**
> 3. ✅ Deploy
>
> **If you skip step 1**, figures will fail to load (they fallback to `/figures/` but cyclone_explorer won't be there).

---

## Conceitos fundamentais

### O que vai para onde

| O que | Onde fica | No Git? | Por quê |
|-------|-----------|---------|---------|
| Figuras geradas (pipeline científico) | `figures/` (raiz do repo) | ❌ gitignored | Output científico — podem ser grandes e se regeneram |
| Figuras publicadas (produção) | Supabase Storage (bucket `figures`) | ❌ | Assets servidos via CDN público |
| Figuras de fallback local | `web/public/figures/` | ✅ | Subconjunto necessário para fallback/offline |
| Manifests JSON | `web/src/content/*.json` | ✅ | Lidos em build-time pelo Next.js |
| Código do site | `web/src/` | ✅ | Obviamente |

### Papel de cada serviço

- **Supabase Storage**: hospeda as figuras como assets públicos via CDN. O site lê as URLs finais do Supabase. **`git push` NÃO faz upload para o Supabase automaticamente** — você precisa rodar o script de upload explicitamente.
- **Vercel**: faz o build do Next.js e publica o site. O deploy acontece automaticamente a cada `git push`. A Vercel não sabe das figuras nem faz upload — ela apenas lê os manifests que já estão no repositório.
- **Manifests JSON** (`web/src/content/`): são a "cola" entre o pipeline científico e o frontend. O frontend só exibe o que está nos manifests. Se uma figura não está no manifest, ela não aparece no site.

### Fluxo preferencial

```
1. Gerar figuras localmente   →   figures/
2. Publicar no Supabase       →   Supabase Storage (bucket 'figures')
3. Regenerar manifests        →   web/src/content/*.json  (URLs do Supabase)
4. git commit + push          →   Vercel faz deploy automático
```

> **Fallback local:** Se o Supabase não estiver configurado, as figuras são servidas de `web/public/figures/` (assets estáticos commitados). Isso funciona mas não é o fluxo recomendado para produção.

---

## Comando único para o dia a dia

O script `scripts/web/prepare_site.py` orquestra todo o pipeline. Use ele como ponto de entrada.

```bash
# Da raiz do repositório:

# Fluxo normal (figuras já geradas, fazer upload e deploy):
python scripts/web/prepare_site.py --skip-science

# Fluxo completo (regenerar figuras + upload + deploy):
python scripts/web/prepare_site.py

# Só atualizar manifests e commitar (sem upload):
python scripts/web/prepare_site.py --skip-science --no-upload

# Preview sem fazer nada:
python scripts/web/prepare_site.py --dry-run
```

O script executa, em ordem:
1. [opcional] Pipeline científico (`step4_create_figures.py`, `step5_update_scientific_notes.py`)
2. Copia figuras para `web/public/figures/` (fallback local)
3. Regenera **todos** os manifests JSON (`build_site_manifest.py`, `extract_cluster_site_data.py`, `extract_composite_site_data.py`, `extract_ck_subterms_site_data.py`)
4. [opcional] Upload para Supabase Storage (se `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estiverem definidos)
5. [opcional] `git add` + `git commit` + `git push`

Equivalente via npm (na pasta `web/`):
```bash
cd web
npm run prepare-site          # --skip-science --no-commit
npm run prepare-site:full     # pipeline completo --no-commit
npm run prepare-site:deploy   # --skip-science (inclui commit+push)
```

---

## Primeira configuração

### Pré-requisitos

- Python 3.9+
- Node.js 18+ (para o build local)
- Conta no GitHub com o repositório criado
- Conta no Supabase (recomendado para produção)
- Conta na Vercel

### Variáveis de ambiente necessárias

Para o upload para o Supabase, defina na sua máquina (`.env.local` ou shell):

```bash
export SUPABASE_URL=https://xxxxxxxx.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=eyJ...   # chave service_role (não a anon key)
```

Para o site em produção (configurar no painel da Vercel):

| Variável | Valor | Obrigatória? |
|----------|-------|-------------|
| `NEXT_PUBLIC_SUPABASE_FIGURES_URL` | `https://xxxxxxxx.supabase.co/storage/v1/object/public/figures` | Sim (para URLs do Supabase) |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxxxxx.supabase.co` | Não (para banco de dados) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Não (para banco de dados) |

> Se `NEXT_PUBLIC_SUPABASE_FIGURES_URL` não estiver definida, o site usará as figuras de `web/public/figures/` (fallback local).

### Criar o bucket no Supabase

1. No painel Supabase → **Storage** → **New bucket**
2. Nome: `figures`
3. Marcar como **Public**
4. Confirmar

### Configurar na Vercel

1. Importar o repositório na Vercel
2. **Root Directory**: `web` (crítico — sem isso o build falha)
3. **CRITICAL:** Do NOT add `NEXT_PUBLIC_SUPABASE_FIGURES_URL` until figures are uploaded (see below)

⚠️ **WARNING:** Setting `NEXT_PUBLIC_SUPABASE_FIGURES_URL` without uploading figures will cause all images to fail loading with fallback to local assets. The site will work, but figures may not load if they're not in `web/public/figures/`.

### Upload inicial das figuras (REQUIRED before setting env var)

**IMPORTANT:** Upload figures to Supabase BEFORE setting `NEXT_PUBLIC_SUPABASE_FIGURES_URL` in Vercel.

```bash
# Da raiz do repositório:
python scripts/web/upload_figures_to_supabase.py --dry-run   # preview
python scripts/web/upload_figures_to_supabase.py             # upload real

# CRITICAL: Upload includes ALL directories:
#  - cluster/
#  - main/
#  - ep_structure/      (composite figures)
#  - ck_subterms/
#  - cyclone_explorer/  (excluded from git/vercel but MUST be in Supabase)
```

O script imprime o valor exato de `NEXT_PUBLIC_SUPABASE_FIGURES_URL` ao final.

**After successful upload:**
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add `NEXT_PUBLIC_SUPABASE_FIGURES_URL` with the value printed by the script
3. Redeploy the site

---

## Fluxo: atualizar figuras existentes

Use este fluxo quando as análises científicas são regeneradas.

```bash
# 1. Regenerar figuras (pipeline científico)
python scripts/ep_structure_analysis/step4_create_figures.py
python scripts/ep_structure_analysis/step5_update_scientific_notes.py
# e/ou outros scripts de análise, ex:
python scripts/ck_subterms_analysis/step3_validate_and_figures.py

# 2. Pipeline web completo
python scripts/web/prepare_site.py --skip-science
```

O `prepare_site.py` faz:
- Copia figuras para `web/public/figures/`
- Regenera todos os manifests
- Faz upload para Supabase (se credenciais disponíveis)
- Commit + push → Vercel faz redeploy automático

---

## Fluxo: adicionar uma nova análise ao site

Quando você cria uma nova análise científica e quer exibi-la no site:

### 1. Gerar as figuras da nova análise

```bash
python scripts/nova_analise/gerar_figuras.py
# → Figuras em: figures/nova_analise/*.png
```

### 2. Criar o extrator de manifest

Crie `scripts/web/extract_nova_analise_site_data.py` seguindo o padrão de `extract_ck_subterms_site_data.py`:
- Lê os resultados de `results/nova_analise/`
- Gera `web/src/content/nova_analise_manifest.json`
- Define as URLs das figuras (Supabase ou fallback local)

### 3. Registrar o extrator em `prepare_site.py`

Adicione o novo extrator na lista `manifest_scripts` dentro do Step 3 de `scripts/web/prepare_site.py`:

```python
manifest_scripts = [
    ...
    ("scripts/web/extract_nova_analise_site_data.py", "extract_nova_analise_site_data.py"),
]
```

### 4. Criar a página no Next.js

Crie `web/src/app/analyses/nova-analise/page.tsx`:
- Leia o manifest com `readManifest('nova_analise_manifest.json')`
- Use os componentes de `web/src/components/analysis/`
- Use `figureUrl()` para as URLs das figuras (lê de manifest ou fallback)

### 5. Adicionar à navegação (se necessário)

Verifique se a nova análise precisa aparecer em `web/src/app/analyses/page.tsx` ou na navegação lateral.

### 6. Rodar o pipeline completo

```bash
python scripts/web/prepare_site.py --skip-science
```

### Checklist para nova análise

- [ ] Figuras geradas em `figures/nova_analise/`
- [ ] Extrator de manifest criado e testado individualmente
- [ ] Extrator registrado em `prepare_site.py`
- [ ] Manifest JSON em `web/src/content/` com URLs corretas
- [ ] Página Next.js criada e funcionando localmente (`npm run dev`)
- [ ] `npm run build` passa sem erros
- [ ] Upload para Supabase feito
- [ ] `git push` feito → Vercel fez redeploy

---

## Scripts em `scripts/web/` — referência rápida

| Script | Propósito | Quando usar |
|--------|-----------|-------------|
| `prepare_site.py` | **Orchestrador principal** — use este no dia a dia | Sempre que quiser atualizar o site |
| `upload_figures_to_supabase.py` | Upload de figuras para Supabase Storage | Chamado automaticamente pelo `prepare_site.py`; use diretamente para re-upload seletivo |
| `copy_figures_to_web.py` | Copia figuras para `web/public/figures/` (fallback local) | Chamado automaticamente pelo `prepare_site.py` |
| `build_site_manifest.py` | Gera `cluster_manifest.json`, `figures_manifest.json`, `documents_manifest.json` | Chamado automaticamente pelo `prepare_site.py` |
| `extract_cluster_site_data.py` | Gera manifests de PCA e K-Means (steps 2-4) | Chamado automaticamente pelo `prepare_site.py` |
| `extract_composite_site_data.py` | Gera manifest de análise composta | Chamado automaticamente pelo `prepare_site.py` |
| `extract_ck_subterms_site_data.py` | Gera manifest da análise de subtermos Ck | Chamado automaticamente pelo `prepare_site.py` |
| `test_composite_json_fields.py` | Valida campos do manifest de composites | Uso em desenvolvimento/debugging |

> **Regra geral:** use `prepare_site.py`. Os outros scripts são auxiliares chamados por ele.

### Método canônico de compósitos (Apr 2026)

A análise de compósitos usa um único método fixo: **timesteps centrais da fase de intensificação** (2 se N par, 3 se N ímpar). Não há flag `--mode`.

Para gerar os assets de compósitos:
```bash
# Figuras (EP1, EP2, EP3, EPALL — painéis 2×2 e anomalias EPALL-relativas 1×3)
python scripts/ep_structure_analysis/step4_create_figures.py

# Stats JSON
python scripts/ep_structure_analysis/step5_update_scientific_notes.py

# Web manifests
python scripts/web/extract_composite_site_data.py

# Copiar figuras para web/public/
python scripts/web/copy_figures_to_web.py
```

---

## O que NÃO acontece automaticamente

- `git push` **NÃO** faz upload para o Supabase. O upload é sempre manual (via `prepare_site.py` ou diretamente `upload_figures_to_supabase.py`).
- A Vercel **NÃO** lê figuras do repositório local — ela só consome os manifests JSON (commitados) e serve assets de `web/public/figures/` (também commitados).
- Se você regenerou figuras mas **não rodou o upload** para o Supabase, o site em produção continuará mostrando as figuras antigas.
- Se você regenerou figuras mas **não regenerou os manifests**, as páginas do site podem mostrar dados desatualizados.

---

## Desenvolvimento local

```bash
cd web
npm install
npm run dev
# → http://localhost:3000
```

As figuras são servidas de `web/public/figures/`. Se `NEXT_PUBLIC_SUPABASE_FIGURES_URL` não estiver em `.env.local`, o fallback local é usado — nenhuma configuração extra necessária para desenvolvimento.

Para simular o Supabase localmente, crie `web/.env.local`:
```
NEXT_PUBLIC_SUPABASE_FIGURES_URL=https://xxxxxxxx.supabase.co/storage/v1/object/public/figures
```

---

## Bundle Size Management (Vercel Function Limits)

### The Problem

Vercel has a **300 MB limit** per serverless function. When deploying Next.js with large static assets in `public/`, each route's function may include a copy of those assets, causing deployment failures like:

```
The Vercel Function "analyses/ck-subterms.rsc" is 309.78mb which exceeds the maximum size limit of 300mb
```

### Root Cause: cyclone_explorer

The `public/figures/cyclone_explorer/` directory contains **498 files (211 MB)**—panels for individual cyclone exploration. This is too large to bundle with every serverless function.

### Solution Architecture

**DO:**
- ✅ Store large asset collections (cyclone_explorer) **exclusively in Supabase Storage**
- ✅ Use `.vercelignore` to exclude them from deployment
- ✅ Keep manifests pointing to Supabase URLs
- ✅ Only commit small, essential fallback figures to `public/`

**DON'T:**
- ❌ Commit 200+ MB of cyclone panels to `web/public/`
- ❌ Import large JSON manifests directly in page components
- ❌ Serialize heavy data structures in React Server Components
- ❌ Assume "it builds locally" means it will deploy to Vercel

### Implementation

1. **`.vercelignore` (already configured):**
   ```
   # Exclude large cyclone_explorer figures from Vercel deployment
   public/figures/cyclone_explorer/
   ```

2. **Upload to Supabase:**
   ```bash
   python scripts/web/upload_figures_to_supabase.py --dirs cyclone_explorer
   ```

3. **Verify manifest URLs point to Supabase:**
   ```bash
   grep "cyclone_explorer" web/src/content/cyclone_explorer_manifest.json | head -3
   # Should show: https://xxx.supabase.co/storage/v1/object/public/figures/cyclone_explorer/...
   ```

4. **Set environment variable in Vercel:**
   ```
   NEXT_PUBLIC_SUPABASE_FIGURES_URL=https://<project>.supabase.co/storage/v1/object/public/figures
   ```

5. **Clean up local public/ (optional):**
   ```bash
   # cyclone_explorer is already .gitignored, so it won't be committed
   # But if it exists locally, you can remove it:
   rm -rf web/public/figures/cyclone_explorer/
   ```

### Prevention Guidelines

When adding new content to the site:

| Content Type | Max Size | Storage Strategy |
|--------------|----------|------------------|
| Individual figures (cluster, composites, ck_subterms) | <5 MB each | Supabase preferred, `public/` fallback OK |
| Large collections (cyclone_explorer, animations) | >50 MB total | **Supabase only**, exclude from `public/` |
| Manifests (JSON) | <200 KB each | Committed to `web/src/content/` |
| Page bundles (per route) | <10 MB | Keep imports minimal, lazy-load heavy components |

### What NOT to do

❌ **Bad Pattern 1: Importing large manifests in page.tsx**
```typescript
// DON'T: Serializes entire manifest into RSC payload
import fullData from '@/content/huge_manifest.json'
```

✅ **Good Pattern: Load on-demand**
```typescript
// Server Component reads at build time, doesn't serialize
const data = readManifest('huge_manifest.json')
// Only pass minimal props to Client Components
```

❌ **Bad Pattern 2: Committing large figure collections**
```bash
# DON'T
git add web/public/figures/cyclone_explorer/*.png  # 498 files
```

✅ **Good Pattern: Supabase + .vercelignore**
```bash
# DO
python scripts/web/upload_figures_to_supabase.py --dirs cyclone_explorer
echo "public/figures/cyclone_explorer/" >> web/.vercelignore
```

❌ **Bad Pattern 3: Assuming local build = Vercel build**
```bash
npm run build  # ✓ Passes locally
git push       # ✗ Fails on Vercel (function size limit)
```

✅ **Good Pattern: Verify bundle size**
```bash
# Check what's included in build
du -sh web/.next/standalone/  # Should be <50 MB
du -sh web/public/figures/*/  # Should exclude cyclone_explorer
```

### Monitoring Bundle Size

After deployment, check function sizes:
- Vercel Dashboard → Deployment Details → Functions tab
- All routes should be **< 50 MB** (well below 300 MB limit)

If any route exceeds 100 MB:
1. Identify what's being bundled (check imports in that route's `page.tsx`)
2. Move large assets to Supabase
3. Add exclusions to `.vercelignore`
4. Ensure manifests use Supabase URLs

---

## Troubleshooting

### Figura não aparece no site (ícone quebrado)

1. **Verificar se o upload para Supabase foi feito:**
   ```bash
   python scripts/web/upload_figures_to_supabase.py --dry-run
   ```
   Se a figura aparecer como "seria enviada", o upload ainda não foi feito. Rode sem `--dry-run`.

2. **Verificar se o manifest aponta para a URL correta:**
   ```bash
   cat web/src/content/ck_subterms_manifest.json | grep boxplots
   ```
   A URL deve ser `https://...supabase.co/storage/.../ck_subterms/ck_subterms_boxplots.png`.

3. **Verificar o fallback local:**
   ```bash
   git ls-files web/public/figures/ | grep ck_subterms
   ```
   Se vazio, rode `python scripts/web/copy_figures_to_web.py` e commit.

4. **Verificar se a variável de ambiente está configurada na Vercel:**
   Painel Vercel → Settings → Environment Variables → verificar `NEXT_PUBLIC_SUPABASE_FIGURES_URL`.

### Manifest aponta para caminho local em vez de URL Supabase

O extrator de manifest usa `SUPABASE_FIGURES_URL` ou `NEXT_PUBLIC_SUPABASE_FIGURES_URL` do ambiente. Se nenhuma das duas estiver definida quando o extrator foi rodado, o manifest fica com caminhos locais.

```bash
export NEXT_PUBLIC_SUPABASE_FIGURES_URL=https://xxx.supabase.co/storage/v1/object/public/figures
python scripts/web/extract_ck_subterms_site_data.py
git add web/src/content/ck_subterms_manifest.json
git commit -m "fix: update manifest with Supabase URLs"
git push
```

### Análise adicionada mas não aparece no site

1. O extrator foi registrado em `prepare_site.py`? (lista `manifest_scripts` no Step 3)
2. O manifest JSON foi gerado em `web/src/content/`?
3. A página Next.js lê esse manifest?
4. O link para a página existe na navegação?

### Build quebra no Vercel ("module not found", TypeScript error)

1. Reproduzir localmente:
   ```bash
   cd web
   npm run typecheck
   npm run build
   ```
2. Se passar localmente, pode ser cache da Vercel — forçar redeploy:
   - Vercel → Deployments → ⋯ → Redeploy (sem cache)
3. Erro de CSS import em Server Component:
   - Componentes que importam CSS (ex: KaTeX) **devem** ter `'use client'` (com aspas, primeira linha do arquivo).
4. Erro de import de módulo client-side em API route:
   - API routes (`app/api/`) são server-only. Nunca importe componentes de UI nelas.

### `npm run build` falha com erro de InlineMath / KaTeX

O componente `web/src/components/analysis/InlineMath.tsx` deve começar com `'use client'` (string literal, com aspas). Sem aspas, Next.js trata o componente como Server Component e o import de CSS falha.

### Bucket/path incorreto no Supabase

A URL esperada segue o padrão:
```
https://<project>.supabase.co/storage/v1/object/public/figures/<subdir>/<file>.png
```
O bucket deve se chamar `figures` e ser público. Os arquivos são enviados com a estrutura de diretórios preservada (ex: `ck_subterms/ck_subterms_boxplots.png`).

### Deploy automático não aconteceu

- Verifique se o push chegou ao GitHub: `git log --oneline -3`
- Verifique os Deployments na Vercel — pode haver um erro de build
- **Root Directory** deve ser `web` nas configurações do projeto na Vercel

---

## O que commitar vs. não commitar

### ✅ Deve estar no Git

| Arquivo | Por quê |
|---------|---------|
| `web/public/figures/` | Fallback estático das figuras (subconjunto pequeno) |
| `web/src/content/*.json` | Manifests lidos em build-time pelo Next.js |
| `results/ep_structure/composite_stats_*.json` | Estatísticas científicas para ambos os modos de compósitos |
| `scripts/web/*.py` | Scripts operacionais |
| `web/**/*.ts`, `web/**/*.tsx` | Código do site |
| `web/DEPLOYMENT.md` | Este guia |

### ❌ NÃO deve estar no Git

| Arquivo | Por quê |
|---------|---------|
| `figures/**/*.png` | Output científico bruto — gitignored |
| `data/**/*.nc` | Dados ERA5 pesados |
| `web/.env.local` | Segredos — só na sua máquina |
| `web/node_modules/` | Instalado pela Vercel |
| `web/.next/` | Gerado pela Vercel |

---

## Redeploy manual

```bash
# Opção 1: commit vazio
git commit --allow-empty -m "chore: trigger redeploy"
git push

# Opção 2: pelo painel
# Vercel → Deployments → ⋯ → Redeploy
```
