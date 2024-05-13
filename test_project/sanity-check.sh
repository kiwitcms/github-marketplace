#!/bin/bash -xe

echo "----- Sanity test - boot the docker image -----"
docker-compose up -d
docker-compose logs -f -t > docker-compose.log &
sleep 5

IP_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' web`
echo "--- web.example.bg: $IP_ADDRESS --"
sudo sh -c "echo '$IP_ADDRESS    testing.example.bg' >> /etc/hosts"


echo "----- Sanity test - initial configuration ----"
# need to monkey-patch createsuperuser.py b/c it rejects input when not using a TTY
docker exec -i web sed -i "s/raise NotRunningInTTYException/pass/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py
docker exec -i web sed -i "s/getpass.getpass/input/" /venv/lib64/python3.11/site-packages/django/contrib/auth/management/commands/createsuperuser.py
echo -e "super-root\nroot@example.com\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\nsecret-2a9a34cd-e51d-4039-b709-b45f629a5595\n" | docker exec -i web /Kiwi/manage.py initial_setup

echo "----- Sanity test - login page ----"
curl -k -L -o page.html https://testing.example.bg:8443/


echo "----- Sanity test - shutdown the docker image -----"
docker-compose down
