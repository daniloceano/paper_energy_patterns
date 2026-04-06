# 🔧 Correção: Detecção de Casos Já Processados

**Data:** 2026-03-25  
**Arquivo:** `scripts/ck_subterms_analysis/step2_run_lec_toolkit.py`  
**Status:** ✅ **CORRIGIDO**

---

## 🐛 Problema Identificado

O script `step2_run_lec_toolkit.py` **NÃO estava detectando corretamente** casos já processados, causando re-processamento desnecessário de ciclones completados.

### Comportamento Incorreto

Ao executar o script, casos que já haviam sido processados eram **re-executados** ao invés de serem **pulados**.

---

## 🔍 Causa Raiz

A função `is_already_processed(track_id)` estava procurando por arquivos com nomes **incorretos**:

### O que a função procurava (ERRADO):
```python
# Arquivos procurados (não existem!)
result_dir / "results.csv"          # ❌ Nome errado
result_dir / "periods.csv"          # ❌ Não gerado
result_dir / "*_level.csv"          # ❌ Não gerado nesta versão
```

### O que o LorenzCycleToolkit gera (CORRETO):
```python
# Arquivos realmente gerados
result_dir / f"{track_id}_ERA5_track_results.csv"     # ✅ Nome completo
result_dir / f"{track_id}_ERA5_track_trackfile"       # ✅ Trackfile
result_dir / "results_vertical_levels/"               # ✅ Diretório
result_dir / f"log.{track_id}_ERA5"                   # ✅ Log
```

### Resultado do Bug

```
Função original:
  is_already_processed('19810096') → False, None  ❌ ERRADO!
  
Realidade:
  19810096_ERA5_track_results.csv EXISTE! ✅
  
Consequência:
  Script tentaria processar NOVAMENTE o caso 19810096! ❌
```

---

## ✅ Correção Implementada

### Mudanças na Função `is_already_processed()`

```python
def is_already_processed(track_id):
    """
    Check if LEC has already been computed for this cyclone.
    
    CORREÇÃO: Agora procura pelo arquivo correto gerado pelo LorenzCycleToolkit:
    - Primary check: {track_id}_ERA5_track_results.csv
    - Fallback checks: mantidos para retrocompatibilidade
    """
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if result_dir.exists():
        # ✅ CORREÇÃO: Verificar arquivo com nome completo
        results_csv = result_dir / f"{track_id}_ERA5_track_results.csv"
        
        if results_csv.exists():
            return True, 'project'
        
        # Fallback para formatos antigos (retrocompatibilidade)
        possible_files = [
            result_dir / "results.csv",
            result_dir / "periods.csv",
        ]
        level_files = list(result_dir.glob("*_level.csv"))
        
        if any(f.exists() for f in possible_files) or len(level_files) > 0:
            return True, 'project'
    
    # Mesma lógica para diretório do LorenzCycleToolkit
    lorenz_result_dir = LORENZ_RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if lorenz_result_dir.exists():
        results_csv = lorenz_result_dir / f"{track_id}_ERA5_track_results.csv"
        
        if results_csv.exists():
            return True, 'lorenz'
        
        # Fallback
        possible_files = [
            lorenz_result_dir / "results.csv",
            lorenz_result_dir / "periods.csv",
        ]
        level_files = list(lorenz_result_dir.glob("*_level.csv"))
        
        if any(f.exists() for f in possible_files) or len(level_files) > 0:
            return True, 'lorenz'
    
    return False, None
```

---

## 🧪 Validação da Correção

### Teste 1: Casos Recentemente Completados

Testei com 5 casos que foram processados em 2026-03-19:

| Track ID | Função Original | Função Corrigida | Status |
|----------|-----------------|------------------|--------|
| 19810096 | ❌ False, None  | ✅ True, 'project' | ✅ OK  |
| 19801105 | ❌ False, None  | ✅ True, 'project' | ✅ OK  |
| 19800614 | ❌ False, None  | ✅ True, 'project' | ✅ OK  |
| 19800640 | ❌ False, None  | ✅ True, 'project' | ✅ OK  |
| 19800455 | ❌ False, None  | ✅ True, 'project' | ✅ OK  |

**Resultado:** Todos os casos completados agora são detectados corretamente! ✅

### Teste 2: Análise Completa (444 casos)

```
Total de tracks:                444
Detectados como completed:      387 (87.2%)
Detectados como NOT completed:   57 (12.8%)
```

**Consistência com disco:**
```
Diretórios em lec_results/:           389
Diretórios com *_results.csv:         387  ✅ MATCH
```

### Teste 3: Simulação de Execução

Simulei o que aconteceria ao executar o script:

```
Total de casos:                 444
Seriam PULADOS (já processados): 387  ✅
Seriam PROCESSADOS (novos):       57  ✅

Exemplos de casos que seriam pulados:
  ✓ 19790135 (found in project)
  ✓ 19790166 (found in project)
  ✓ 19810096 (found in project)  ← Este seria re-processado antes!
  ✓ 19801105 (found in project)  ← Este seria re-processado antes!
  ... e mais 383

Exemplos de casos que seriam processados (pending):
  ⏳ 19810394
  ⏳ 19810742
  ⏳ 19810971
  ... e mais 54
```

**Resultado:** Script agora pula corretamente casos já processados! ✅

---

## 📊 Impacto da Correção

### Antes (Função Bugada)

```
❌ Comportamento incorreto:
   - 387 casos completados NÃO eram detectados
   - Script tentaria re-processar TODOS os 444 casos
   - Desperdício massivo de tempo e recursos computacionais
   - Risco de sobrescrever resultados válidos
```

### Depois (Função Corrigida)

```
✅ Comportamento correto:
   - 387 casos completados são detectados e PULADOS
   - Script processa apenas os 57 casos pendentes
   - Economia de ~387 × 5.75 min = ~37 horas de processamento!
   - Resultados válidos preservados
```

---

## 🎯 Como Usar o Script Corrigido

### Execução Normal

```bash
# O script agora pula automaticamente casos já processados
python scripts/ck_subterms_analysis/step2_run_lec_toolkit.py
```

**Output esperado:**
```
Checking processing status...

   Already processed: 387/444
   Already processed cases will be skipped

Processing 444 EP1 cyclones with LorenzCycleToolkit...
   Parallel workers: 5

   Progress (completed/total):
   [1/444] 19790135 - ✓ Already processed (found in project) (skipping)
   [2/444] 19790166 - ✓ Already processed (found in project) (skipping)
   ...
   [388/444] 19810394 - Starting processing...  ← Primeiro caso novo
   ...
```

### Verificação Manual

Para verificar quantos casos serão pulados:

```bash
cd /p1-swell/danilocs/paper_energy_patterns

python3 -c "
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

import importlib.util
spec = importlib.util.spec_from_file_location('step2', 'scripts/ck_subterms_analysis/step2_run_lec_toolkit.py')
step2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(step2)

tracks_dir = Path('data/ck_analysis/tracks')
track_files = sorted(tracks_dir.glob('track_*.txt'))

completed = sum(1 for f in track_files if step2.is_already_processed(f.stem.replace('track_', ''))[0])
total = len(track_files)

print(f'Completed: {completed}/{total} ({completed/total*100:.1f}%)')
print(f'Pending: {total - completed}/{total} ({(total-completed)/total*100:.1f}%)')
"
```

---

## 📝 Checklist de Validação

- [x] Bug identificado (nome de arquivo incorreto)
- [x] Causa raiz documentada
- [x] Correção implementada
- [x] Testado com casos completados (5 casos: 100% sucesso)
- [x] Testado com análise completa (444 casos)
- [x] Validado consistência com disco (387 = 387 ✓)
- [x] Simulação de execução confirmada
- [x] Impacto quantificado (~37h economizadas)
- [x] Documentação atualizada
- [x] Retrocompatibilidade mantida (fallback para formatos antigos)

---

## ✅ Conclusão

**Status:** ✅ **BUG CORRIGIDO E VALIDADO**

A função `is_already_processed()` agora:
- ✅ Detecta corretamente casos já processados (387/387)
- ✅ Pula automaticamente casos completados
- ✅ Processa apenas casos novos/pending (57)
- ✅ Economiza ~37 horas de processamento
- ✅ Preserva resultados válidos existentes

**Você pode agora executar o script com segurança!** Casos já processados serão automaticamente pulados.

---

**Correção realizada por:** GitHub Copilot  
**Data:** 2026-03-25  
**Arquivo modificado:** `scripts/ck_subterms_analysis/step2_run_lec_toolkit.py`  
**Linhas modificadas:** Função `is_already_processed()` (linhas 283-345)

