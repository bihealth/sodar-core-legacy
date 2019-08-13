#!/usr/bin/env bash

echo "***********************************************"
echo "Setting up Database and User for PostgreSQL"
echo "***********************************************"

# while loops to ensure input not empty

while [[ -z "$db_name" ]]
do
    echo -n "Database Name: "
    read db_name
done

while [[ -z "$username" ]]
do
    echo -n "Username: "
    read username
done

while [[ -z "$password" ]]
do
    echo -n "Password: "
    read password
done

sudo su -c "psql -c \"CREATE DATABASE $db_name;\"" postgres
sudo su -c "psql -c \"CREATE USER $username WITH PASSWORD '$password';\"" postgres
sudo su -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $db_name to $username;\"" postgres
sudo su -c "psql -c \"ALTER USER $username CREATEDB;\"" postgres
