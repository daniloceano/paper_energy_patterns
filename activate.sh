#!/bin/bash

# Quick activation script for paper_energy_patterns conda environment

ENV_NAME="paper_energy_patterns"

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

echo "✅ Activated: $ENV_NAME"
echo "Python: $(which python)"
echo "Version: $(python --version)"
