#!/bin/bash
# Install PyDMD for Dynamic Mode Decomposition
# Cherokee AI Federation - Resonance Analysis

source /home/dereadi/cherokee_venv/bin/activate

pip install pydmd numpy scipy matplotlib

# Verify installation
python3 -c "from pydmd import DMD; print('PyDMD installed successfully')"

echo "PyDMD ready for resonance analysis"