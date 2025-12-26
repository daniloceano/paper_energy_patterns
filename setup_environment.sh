#!/bin/bash

# Setup script for paper_energy_patterns conda environment
# This script checks if the environment exists, creates it if needed,
# verifies all packages are installed, and activates the environment

set -e  # Exit on error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="paper_energy_patterns"

echo "Setting up conda environment: $ENV_NAME"
echo "Project directory: $PROJECT_DIR"
echo ""

# Function to check if a package is installed
check_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

# Function to check if all packages from requirements.txt are installed
check_all_packages() {
    echo "Checking installed packages..."
    local missing_packages=()
    
    # Read requirements.txt and check each package
    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^#.* ]] && continue
        
        # Extract package name (before >= or ==)
        package=$(echo "$line" | sed 's/[>=<].*//' | xargs)
        
        # Special cases for packages with different import names
        if [ "$package" = "scikit-learn" ]; then
            import_name="sklearn"
        elif [ "$package" = "lorenz-phase-space" ]; then
            import_name="LEC"
        else
            import_name="$package"
        fi
        
        if ! check_package "$import_name"; then
            missing_packages+=("$package")
        fi
    done < "$PROJECT_DIR/requirements.txt"
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        echo "✅ All packages are installed!"
        return 0
    else
        echo "❌ Missing packages: ${missing_packages[*]}"
        return 1
    fi
}

# Check if conda environment exists
if conda env list | grep -q "^$ENV_NAME "; then
    echo "✅ Environment '$ENV_NAME' already exists"
    
    # Activate environment
    eval "$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
    
    # Check if all packages are installed
    if check_all_packages; then
        echo ""
        echo "🎉 Environment is ready to use!"
    else
        echo ""
        echo "Installing missing packages..."
        pip install -r "$PROJECT_DIR/requirements.txt"
        echo ""
        echo "✅ Missing packages installed!"
    fi
    
else
    echo "Creating new conda environment: $ENV_NAME"
    
    # Create conda environment with Python 3.13
    conda create -n "$ENV_NAME" python=3.13 -y
    
    # Activate environment
    eval "$(conda shell.bash hook)"
    conda activate "$ENV_NAME"
    
    # Install all packages
    echo ""
    echo "Installing packages from requirements.txt..."
    pip install -r "$PROJECT_DIR/requirements.txt"
    
    echo ""
    echo "✅ Environment created and packages installed!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Environment: $ENV_NAME (activated)"
echo "Python: $(which python)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To activate this environment in the future, run:"
echo "  conda activate $ENV_NAME"
echo ""
echo "To verify the installation, run:"
echo "  python scripts/setup_and_examples/verify_environment.py"
