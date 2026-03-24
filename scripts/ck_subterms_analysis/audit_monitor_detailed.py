#!/usr/bin/env python3
"""
audit_monitor_detailed.py - Auditoria Detalhada do Monitor CK

Compara a classificação do monitor atual com o estado real em disco
para cada track_id, identificando inconsistências.

Author: Danilo Couto de Souza
Date: March 2026
"""

import sys
from pathlib import Path
import pandas as pd
import json

sys.path.append(str(Path(__file__).resolve().parents[2]))

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRACKS_DIR = PROJECT_ROOT / "data" / "ck_analysis" / "tracks"
RESULTS_DIR = PROJECT_ROOT / "results" / "ck_analysis" / "lec_results"
LOG_DIR = PROJECT_ROOT / "results" / "ck_analysis" / "logs"
ALL_EP1_CASES_FILE = PROJECT_ROOT / "results" / "ep_structure" / "ep1_cases.csv"

# Arquivos de saída da auditoria
AUDIT_DIR = PROJECT_ROOT / "results" / "ck_analysis"
AUDIT_PER_CASE = AUDIT_DIR / "ck_monitor_audit_per_case.csv"
AUDIT_SUMMARY = AUDIT_DIR / "ck_monitor_audit_summary.json"
AUDIT_REPORT = AUDIT_DIR / "ck_monitor_audit_report.txt"

# ============================================================================
# FUNÇÕES DE CLASSIFICAÇÃO DO ESTADO REAL
# ============================================================================

def classify_real_status(track_id: str) -> dict:
    """
    Classifica o estado REAL de um track_id em disco.
    
    Critérios rigorosos:
    - completed: 
        * Diretório existe
        * Arquivo *_results.csv existe (resultado final do LEC)
        * Subdiretório results_vertical_levels/ existe
        * Log indica "Analysis complete"
    - processing:
        * Diretório existe
        * Alguns arquivos presentes mas não todos os critérios de completed
    - pending:
        * Diretório não existe OU está vazio
    
    Returns:
        dict com keys:
            - status: 'completed', 'processing', 'pending', 'no_track'
            - lec_dir_exists: bool
            - results_csv_exists: bool
            - results_csv_path: str or None
            - vertical_levels_exists: bool
            - log_exists: bool
            - log_has_completion: bool
            - file_count: int
            - notes: str
    """
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    track_file = TRACKS_DIR / f"track_{track_id}.txt"
    
    # Verificar se o track foi preparado
    if not track_file.exists():
        return {
            "status": "no_track",
            "lec_dir_exists": False,
            "results_csv_exists": False,
            "results_csv_path": None,
            "vertical_levels_exists": False,
            "log_exists": False,
            "log_has_completion": False,
            "file_count": 0,
            "notes": "Track file not prepared yet"
        }
    
    # Verificar se o diretório de resultados existe
    if not result_dir.exists():
        return {
            "status": "pending",
            "lec_dir_exists": False,
            "results_csv_exists": False,
            "results_csv_path": None,
            "vertical_levels_exists": False,
            "log_exists": False,
            "log_has_completion": False,
            "file_count": 0,
            "notes": "Result directory not created yet"
        }
    
    # Contar arquivos no diretório
    try:
        file_count = sum(1 for f in result_dir.rglob("*") if f.is_file())
    except Exception:
        file_count = 0
    
    # Verificar arquivo de resultados CSV
    results_csv_candidates = list(result_dir.glob("*_results.csv"))
    results_csv_exists = len(results_csv_candidates) > 0
    results_csv_path = str(results_csv_candidates[0].name) if results_csv_exists else None
    
    # Verificar subdiretório de níveis verticais
    vertical_levels_dir = result_dir / "results_vertical_levels"
    vertical_levels_exists = vertical_levels_dir.exists() and vertical_levels_dir.is_dir()
    
    # Verificar log e mensagem de conclusão
    log_file = result_dir / f"log.{track_id}_ERA5"
    log_exists = log_file.exists()
    log_has_completion = False
    
    if log_exists:
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            for line in lines[-10:]:
                if 'Analysis complete' in line or 'ran in' in line:
                    log_has_completion = True
                    break
        except Exception:
            pass
    
    # Determinar status
    if results_csv_exists and vertical_levels_exists and log_has_completion:
        status = "completed"
        notes = "All completion criteria met"
    elif file_count > 5:  # Alguns arquivos presentes
        status = "processing"
        notes = f"Partial results ({file_count} files)"
        if not results_csv_exists:
            notes += ", no results CSV"
        if not vertical_levels_exists:
            notes += ", no vertical_levels dir"
        if not log_has_completion:
            notes += ", log incomplete"
    else:
        status = "pending"
        notes = f"Directory exists but mostly empty ({file_count} files)"
    
    return {
        "status": status,
        "lec_dir_exists": True,
        "results_csv_exists": results_csv_exists,
        "results_csv_path": results_csv_path,
        "vertical_levels_exists": vertical_levels_exists,
        "log_exists": log_exists,
        "log_has_completion": log_has_completion,
        "file_count": file_count,
        "notes": notes
    }


def classify_monitor_status(track_id: str) -> str:
    """
    Simula a classificação do MONITOR ATUAL (lógica do step2_monitor_ck.py).
    
    Returns: 'completed', 'in_progress', 'pending', or 'no_track'
    """
    track_file = TRACKS_DIR / f"track_{track_id}.txt"
    
    if not track_file.exists():
        return 'no_track'
    
    result_dir = RESULTS_DIR / f"{track_id}_ERA5_track"
    
    if not result_dir.exists():
        return 'pending'
    
    # O monitor atual usa apenas dois padrões para classificar como "completed"
    RESULT_FILE_PATTERNS = ["*_results.csv", "*_trackfile"]
    
    for pattern in RESULT_FILE_PATTERNS:
        matching_files = list(result_dir.glob(pattern))
        if len(matching_files) > 0:
            return 'completed'
    
    # Também checa log
    log_file = result_dir / f"log.{track_id}_ERA5"
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            for line in lines[-5:]:
                if 'Analysis complete' in line or 'ran in' in line:
                    return 'completed'
        except Exception:
            pass
    
    return 'in_progress'


# ============================================================================
# AUDITORIA
# ============================================================================

def run_audit():
    """
    Executa auditoria completa comparando monitor vs estado real.
    """
    print("=" * 80)
    print("AUDITORIA DETALHADA DO MONITOR CK")
    print("=" * 80)
    print()
    
    # Carregar lista de casos esperados
    if not ALL_EP1_CASES_FILE.exists():
        print(f"❌ ERRO: Arquivo {ALL_EP1_CASES_FILE} não encontrado!")
        return
    
    df_expected = pd.read_csv(ALL_EP1_CASES_FILE)
    expected_ids = [str(tid) for tid in df_expected['track_id'].tolist()]
    
    print(f"✅ Casos esperados (ep1_cases.csv): {len(expected_ids)}")
    print()
    
    # Auditar cada caso
    audit_results = []
    
    print("Auditando cada track_id...")
    for i, track_id in enumerate(expected_ids, 1):
        if i % 50 == 0:
            print(f"  Progresso: {i}/{len(expected_ids)}")
        
        # Estado real
        real = classify_real_status(track_id)
        
        # Classificação do monitor
        monitor_status = classify_monitor_status(track_id)
        
        # Comparar
        match = (real['status'] == monitor_status)
        
        audit_results.append({
            'track_id': track_id,
            'monitor_classification': monitor_status,
            'real_classification': real['status'],
            'classification_match': match,
            'lec_dir_exists': real['lec_dir_exists'],
            'results_csv_exists': real['results_csv_exists'],
            'results_csv_path': real['results_csv_path'],
            'vertical_levels_exists': real['vertical_levels_exists'],
            'log_exists': real['log_exists'],
            'log_has_completion': real['log_has_completion'],
            'file_count': real['file_count'],
            'notes': real['notes']
        })
    
    print(f"  Concluído: {len(expected_ids)}/{len(expected_ids)}")
    print()
    
    # Criar DataFrame
    df_audit = pd.DataFrame(audit_results)
    
    # Estatísticas gerais
    print("=" * 80)
    print("ESTATÍSTICAS GERAIS")
    print("=" * 80)
    print()
    
    # Por classificação do monitor
    monitor_counts = df_audit['monitor_classification'].value_counts()
    print("Classificação segundo o MONITOR:")
    for status in ['completed', 'in_progress', 'pending', 'no_track']:
        count = monitor_counts.get(status, 0)
        print(f"  {status:15s}: {count:4d}")
    print(f"  {'TOTAL':15s}: {len(df_audit):4d}")
    print()
    
    # Por classificação real
    real_counts = df_audit['real_classification'].value_counts()
    print("Classificação segundo AUDITORIA REAL:")
    for status in ['completed', 'processing', 'pending', 'no_track']:
        count = real_counts.get(status, 0)
        print(f"  {status:15s}: {count:4d}")
    print(f"  {'TOTAL':15s}: {len(df_audit):4d}")
    print()
    
    # Comparação
    n_matches = df_audit['classification_match'].sum()
    n_mismatches = len(df_audit) - n_matches
    
    print(f"Concordância: {n_matches} casos ({n_matches/len(df_audit)*100:.1f}%)")
    print(f"Discordância: {n_mismatches} casos ({n_mismatches/len(df_audit)*100:.1f}%)")
    print()
    
    # Casos com discordância
    if n_mismatches > 0:
        print("=" * 80)
        print("CASOS COM DISCORDÂNCIA")
        print("=" * 80)
        print()
        
        df_mismatch = df_audit[~df_audit['classification_match']].copy()
        
        # Agrupar por tipo de discordância
        discrepancy_groups = df_mismatch.groupby(['monitor_classification', 'real_classification']).size()
        
        print("Tipos de discordância:")
        for (mon, real), count in discrepancy_groups.items():
            print(f"  Monitor: {mon:15s} → Real: {real:15s}  ({count} casos)")
        print()
        
        # Mostrar alguns exemplos
        print("Exemplos de discordância (primeiros 10):")
        for idx, row in df_mismatch.head(10).iterrows():
            print(f"  {row['track_id']}: Monitor={row['monitor_classification']}, Real={row['real_classification']}")
            print(f"    → {row['notes']}")
        print()
    
    # Verificar casos recentes específicos
    print("=" * 80)
    print("VERIFICAÇÃO DE CASOS RECENTES")
    print("=" * 80)
    print()
    
    recent_cases = ['19810096', '19801105', '19800614', '19800640', '19800455']
    print("Casos mencionados como recentemente completados:")
    
    for track_id in recent_cases:
        row = df_audit[df_audit['track_id'] == track_id]
        if len(row) > 0:
            row = row.iloc[0]
            print(f"\n  {track_id}:")
            print(f"    Monitor: {row['monitor_classification']}")
            print(f"    Real:    {row['real_classification']}")
            print(f"    Match:   {row['classification_match']}")
            print(f"    Notas:   {row['notes']}")
        else:
            print(f"\n  {track_id}: ⚠️  NÃO ENCONTRADO na lista esperada!")
    print()
    
    # Salvar resultados
    print("=" * 80)
    print("SALVANDO ARTEFATOS")
    print("=" * 80)
    print()
    
    # 1. CSV detalhado por caso
    df_audit.to_csv(AUDIT_PER_CASE, index=False)
    print(f"✅ Salvou: {AUDIT_PER_CASE}")
    
    # 2. JSON com resumo
    summary = {
        "audit_date": pd.Timestamp.now().isoformat(),
        "total_expected": len(expected_ids),
        "monitor_classification": monitor_counts.to_dict(),
        "real_classification": real_counts.to_dict(),
        "agreement": {
            "matches": int(n_matches),
            "mismatches": int(n_mismatches),
            "match_percentage": float(n_matches / len(df_audit) * 100)
        },
        "discrepancy_types": {
            f"{mon}_to_{real}": int(count)
            for (mon, real), count in discrepancy_groups.items()
        } if n_mismatches > 0 else {},
        "recent_cases_validation": {
            track_id: {
                "monitor": df_audit[df_audit['track_id'] == track_id].iloc[0]['monitor_classification']
                           if len(df_audit[df_audit['track_id'] == track_id]) > 0 else 'NOT_FOUND',
                "real": df_audit[df_audit['track_id'] == track_id].iloc[0]['real_classification']
                        if len(df_audit[df_audit['track_id'] == track_id]) > 0 else 'NOT_FOUND',
                "match": bool(df_audit[df_audit['track_id'] == track_id].iloc[0]['classification_match'])
                         if len(df_audit[df_audit['track_id'] == track_id]) > 0 else False
            }
            for track_id in recent_cases
        }
    }
    
    with open(AUDIT_SUMMARY, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Salvou: {AUDIT_SUMMARY}")
    
    # 3. Relatório em texto
    with open(AUDIT_REPORT, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("RELATÓRIO DE AUDITORIA DO MONITOR CK\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Data: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total esperado: {len(expected_ids)}\n\n")
        
        f.write("CLASSIFICAÇÃO MONITOR:\n")
        for status in ['completed', 'in_progress', 'pending', 'no_track']:
            count = monitor_counts.get(status, 0)
            f.write(f"  {status:15s}: {count:4d}\n")
        f.write(f"\nCLASSIFICAÇÃO REAL:\n")
        for status in ['completed', 'processing', 'pending', 'no_track']:
            count = real_counts.get(status, 0)
            f.write(f"  {status:15s}: {count:4d}\n")
        
        f.write(f"\nCONCORDÂNCIA:\n")
        f.write(f"  Matches:    {n_matches} ({n_matches/len(df_audit)*100:.1f}%)\n")
        f.write(f"  Mismatches: {n_mismatches} ({n_mismatches/len(df_audit)*100:.1f}%)\n\n")
        
        if n_mismatches > 0:
            f.write("DISCREPÂNCIAS:\n")
            for (mon, real), count in discrepancy_groups.items():
                f.write(f"  {mon} → {real}: {count} casos\n")
    
    print(f"✅ Salvou: {AUDIT_REPORT}")
    print()
    
    print("=" * 80)
    print("AUDITORIA CONCLUÍDA")
    print("=" * 80)
    print()
    
    return df_audit, summary


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    df_audit, summary = run_audit()
