#!/usr/bin/env bash
set -e

# Directory of *this* script
this_dir="$( cd "$( dirname "$0" )" && pwd )"
src_dir="$(realpath "${this_dir}/..")"

if [[ "$1" == '--no-venv' ]]; then
    no_venv='1'
fi

if [[ -z "${no_venv}" ]]; then
    venv="${src_dir}/.venv"
    if [[ -d "${venv}" ]]; then
        source "${venv}/bin/activate"
    fi
fi

python_files=("${src_dir}/hotword_precise_lite/"*.py "${src_dir}/setup.py")

# -----------------------------------------------------------------------------

function check_code {
    flake8 "$@"
    pylint "$@"
    mypy "$@"
    black --check "$@"
    isort --check-only "$@"
}

check_code "${python_files[@]}"

# -----------------------------------------------------------------------------

echo "OK"
