#!/usr/bin/env bash
set -euo pipefail

flask --app conectasenai_api.main db upgrade
flask --app conectasenai_api.main db migrate -m "${1:-auto}"
flask --app conectasenai_api.main db upgrade
