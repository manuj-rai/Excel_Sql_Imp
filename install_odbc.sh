#!/bin/bash

# Update system
apt-get update

# Install ODBC prerequisites
apt-get install -y curl gnupg apt-transport-https unixodbc unixodbc-dev

# Add Microsoft repository keys
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

# Add Microsoft SQL Server ODBC repo
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update and install the driver
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
