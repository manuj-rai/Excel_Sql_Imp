#!/bin/bash

# Update and install dependencies
apt-get update && apt-get install -y curl gnupg apt-transport-https unixodbc unixodbc-dev

# Add Microsoft GPG key
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

# Add Microsoft SQL Server repository (for Debian 11)
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update and install the SQL Server ODBC driver
apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17
