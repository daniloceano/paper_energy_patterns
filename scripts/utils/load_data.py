"""
Funções para carregar dados diretamente do GitHub
"""

import pandas as pd
from typing import Optional

# URLs dos dados
TRACKS_URL = "https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/refs/heads/master/tracks_SAt_filtered/tracks_SAt_filtered_with_periods.csv"
ENERGY_BASE_URL = "https://raw.githubusercontent.com/daniloceano/energetic_patterns_cyclones_south_atlantic/master/csv_database_energy_by_periods"


def load_tracks() -> pd.DataFrame:
    """
    Carrega o CSV com as tracks dos ciclones diretamente do GitHub
    
    Returns:
        DataFrame com as tracks dos ciclones
    """
    print("Carregando tracks dos ciclones...")
    df = pd.read_csv(TRACKS_URL)
    print(f"✓ {len(df)} registros carregados")
    print(f"✓ {df['track_id'].nunique()} ciclones únicos")
    return df


def load_energy_by_cyclone(track_id: str) -> Optional[pd.DataFrame]:
    """
    Carrega a energética média de um ciclone específico
    
    Args:
        track_id: ID do ciclone (ex: '19790001')
    
    Returns:
        DataFrame com as médias energéticas por período, ou None se não encontrado
    """
    url = f"{ENERGY_BASE_URL}/{track_id}_averages.csv"
    try:
        # The first column contains the period names (incipient, intensification, etc.)
        df = pd.read_csv(url, index_col=0)
        # Reset index to make period a regular column
        df = df.reset_index()
        df = df.rename(columns={'index': 'period'})
        return df
    except Exception:
        # Silently return None if file not found
        return None


def load_all_energy_data(track_ids: list) -> dict:
    """
    Carrega dados energéticos de múltiplos ciclones
    
    Args:
        track_ids: Lista de IDs dos ciclones
    
    Returns:
        Dicionário {track_id: DataFrame} com os dados de cada ciclone
    """
    energy_data = {}
    total = len(track_ids)
    
    for i, track_id in enumerate(track_ids, 1):
        if i % 100 == 0:
            print(f"Carregando {i}/{total}...")
        
        df = load_energy_by_cyclone(track_id)
        if df is not None:
            energy_data[track_id] = df
    
    print(f"✓ {len(energy_data)} ciclones carregados com sucesso")
    return energy_data


if __name__ == "__main__":
    # Teste básico
    print("=" * 50)
    print("Teste de carregamento de dados")
    print("=" * 50)
    
    # Testa carregamento das tracks
    tracks = load_tracks()
    print(f"\nColunas disponíveis: {list(tracks.columns)}")
    print(f"\nPrimeiras linhas:\n{tracks.head()}")
    
    # Testa carregamento de um ciclone específico
    print("\n" + "=" * 50)
    track_id = tracks['track_id'].iloc[0]
    print(f"Testando carregamento da energética do ciclone {track_id}")
    energy = load_energy_by_cyclone(track_id)
    if energy is not None:
        print(f"✓ Dados carregados: {energy.shape}")
        print(f"\nColunas: {list(energy.columns)}")
