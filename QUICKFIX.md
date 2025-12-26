# Quick Fix for Missing pyarrow

If you get the error "Missing optional dependency 'pyarrow'", run:

```bash
# Activate environment
conda activate paper_energy_patterns

# Install pyarrow
pip install pyarrow>=14.0.0

# Verify installation
python -c "import pyarrow; print(f'pyarrow {pyarrow.__version__} installed')"

# Now run preprocessing again
python scripts/utils/preprocess_data.py
```

## Alternative: Reinstall all requirements

```bash
conda activate paper_energy_patterns
pip install -r requirements.txt
```

## What was fixed

- Added `pyarrow>=14.0.0` to `requirements.txt`
- Translated all messages to English
- Ready for server deployment

Pull the latest changes:
```bash
git pull origin main
pip install -r requirements.txt
```
