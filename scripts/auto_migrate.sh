#!/usr/bin/env bash
set -euo pipefail

flask --app src.main db upgrade
flask --app src.main db migrate -m "${1:-auto}"
flask --app src.main db upgrade
