#!/bin/bash -xe

# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html


echo "----- Boot the docker image -----"
docker compose up -d
docker compose logs -f -t > docker-compose.log &
sleep 5

IP_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web`
echo "--- testing.example.bg: $IP_ADDRESS --"
sudo sh -c "echo '$IP_ADDRESS    testing.example.bg' >> /etc/hosts"


echo "----- Initial setup ----"
# need to monkey-patch createsuperuser.py b/c it rejects input when not using a TTY
docker exec -i web sed -i "s/raise NotRunningInTTYException/pass/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py
docker exec -i web sed -i "s/getpass.getpass/input/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py
echo -e "super-root\nroot@example.com\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\n" | docker exec -i web /Kiwi/manage.py initial_setup


if [ "$CI" == "true" ]; then
    # regenerate new certificate, valid for the hostname used during testing
    docker exec -i web /usr/bin/sscg -v -f \
                            --hostname "testing.example.bg" \
                            --country BG --locality Sofia \
                            --organization "Kiwi TCMS" \
                            --organizational-unit "Quality Engineering" \
                            --ca-file       /Kiwi/static/ca.crt     \
                            --cert-file     /Kiwi/ssl/localhost.crt \
                            --cert-key-file /Kiwi/ssl/localhost.key

    # restart web service so that it uses the new certificate
    docker compose restart web

    # tell Ubuntu to install out own CA
    sudo mkdir -p /usr/local/share/ca-certificates/
    sudo curl -k -o /usr/local/share/ca-certificates/Kiwi_TCMS_CA.crt https://testing.example.bg:8443/static/ca.crt
    sudo update-ca-certificates --fresh --verbose

    # this isn't actually needed, b/c the CA is in the system trust store
    # but we keep it here for reference
    # export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    # export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    # export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
    # export SSL_CERT_DIR=/etc/ssl/certs/
fi

echo "----- Fetch login page ----"
curl --fail -L -o page.html https://testing.example.bg:8443/

echo "----- Execute integration test(s) ----"
python test_project/integration_tests/test_api.py -v

echo "----- Shutdown the docker image -----"
docker compose down
