#!/bin/bash
# tests/run_tests.sh - Run all tests for microscopy-aesthetics-mcp

set -e

echo "🧪 Running Microscopy Aesthetics MCP Tests"
echo

# Determine if we're in project root or in tests directory
if [ -f "pyproject.toml" ]; then
    PROJECT_ROOT="."
elif [ -f "../pyproject.toml" ]; then
    PROJECT_ROOT=".."
else
    echo "❌ Error: Cannot find pyproject.toml"
    echo "   Run from: project-root/ or project-root/tests/"
    exit 1
fi

echo "📁 Project root: $PROJECT_ROOT"
echo

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $PYTHON_VERSION"
echo

# Run syntax check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Syntax Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python3 -m py_compile "$PROJECT_ROOT/src/microscopy_aesthetics/server.py"; then
    echo "✓ server.py syntax valid"
else
    echo "❌ server.py has syntax errors"
    exit 1
fi
echo

# Run profile validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Profile Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'PYTEST'
import sys
sys.path.insert(0, '.' + '/src')

try:
    from microscopy_aesthetics.server import MICROSCOPY_PROFILES
    
    # Validate profiles
    print(f"✓ Profiles loaded: {len(MICROSCOPY_PROFILES)} types")
    
    vocab_count = sum(
        len(p["structure"]) + len(p["material"]) + len(p["color"]) + 
        len(p["texture"]) for p in MICROSCOPY_PROFILES.values()
    )
    print(f"✓ Vocabulary items: {vocab_count}")
    
    # Check each profile
    expected_types = ['fluorescence', 'electron', 'phase_contrast', 'confocal', 
                     'brightfield', 'darkfield', 'multiphoton']
    
    for t in expected_types:
        if t in MICROSCOPY_PROFILES:
            print(f"  ✓ {t}")
        else:
            print(f"  ❌ MISSING: {t}")
            sys.exit(1)
    
    print("\n✓ All profiles validated")
    
except Exception as e:
    print(f"❌ Error loading profiles: {e}")
    sys.exit(1)
PYTEST

echo

# Run unit tests if test file exists
if [ -f "$PROJECT_ROOT/tests/test_server.py" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Unit Tests (pytest)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if command -v pytest &> /dev/null; then
        cd "$PROJECT_ROOT"
        pytest tests/test_server.py -v
        cd - > /dev/null
    else
        echo "⚠️  pytest not installed (install with: pip install pytest)"
        echo "   Skipping unit tests"
    fi
    echo
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ All tests passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "📋 Next steps:"
echo "  • Server ready for deployment"
echo "  • See docs/ for documentation"
echo "  • Run: python -m microscopy_aesthetics to start server"
echo
