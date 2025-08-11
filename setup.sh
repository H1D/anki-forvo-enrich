#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create mypy config
cat > mypy.ini << EOL
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_optional = True
strict_equality = True

[mypy.plugins.qt.*]
init_forbid_dynamic = True

[mypy-anki.*]
ignore_missing_imports = True

[mypy-aqt.*]
ignore_missing_imports = True
EOL

# Run mypy
mypy --config-file mypy.ini src/anki_forvo_enrich/__init__.py 