# /bin/bash
# Description: Prepare psql for telegram-assistant
NEW_USER_PASSWORD=$(pwgen 24 -c1)
psql -c "CREATE DATABASE telegram-assistant;"
psql -c "CREATE USER telegram-assistant WITH PASSWORD '$NEW_USER_PASSWORD';"
psql -c "ALTER DATABASE telegram-assistant OWNER TO telegram-assistant;"
echo "New user: telegram-assistant"
echo "New password: $NEW_USER_PASSWORD"
echo "Database: telegram-assistant"
# End of snippet
