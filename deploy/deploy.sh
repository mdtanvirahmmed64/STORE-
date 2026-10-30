#!/usr/bin/env bash
# কোড আপডেটের পর সার্ভারে চালান:  bash deploy/deploy.sh
set -e
cd /var/www/shopbd
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart shopbd
echo "Deployed!"
