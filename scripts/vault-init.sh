# /bin/bash
# Description: Prepare vault for telegram-assistant

# Prepare kv2 engine
vault secrets enable -path=telegram-assistant kv-v2 

# Prepare approle
vault policy write telegram-assistant vault/policy.hcl
vault auth enable -path=telegram-assistant approle
vault write auth/telegram-assistant/role/telegram-assistant \
    token_policies=["telegram-assistant"] \
    token_type=service \
    secret_id_num_uses=0 \
    token_num_uses=0 \
    token_ttl=24h \
    bind_secret_id=true \
    mount_point="telegram-assistant" \
    secret_id_ttl=0

# Prepare db engine
vault secrets enable -path=telegram-assistant-database database
vault write telegram-assistant-database/config/postgresql \
    plugin_name=postgresql-database-plugin \
    allowed_roles="telegram-assistant" \
    verify_connection=false \
    connection_url="postgresql://{{username}}:{{password}}@localhost:5432/telegram-assistant?sslmode=disable" \
    username="postgres" \
    password="changeme"
vault write telegram-assistant-database/roles/telegram-assistant-bot \
    db_name=postgresql \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT ALL PRIVILEGES ON SCHEMA public TO \"{{name}}\"; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";" \
    revocation_statements="REVOKE ALL PRIVILEGES ON SCHEMA public FROM \"{{name}}\"; REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM \"{{name}}\"; DROP ROLE \"{{name}}\";" \
    default_ttl="24h" \
    max_ttl="72h"
vault write telegram-assistant-database/roles/telegram-assistant-users \
    db_name=postgresql \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT ALL PRIVILEGES ON SCHEMA public TO \"{{name}}\"; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";" \
    revocation_statements="REVOKE ALL PRIVILEGES ON SCHEMA public FROM \"{{name}}\"; REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM \"{{name}}\"; DROP ROLE \"{{name}}\";" \
    default_ttl="24h" \
    max_ttl="72h"
vault write telegram-assistant-database/roles/telegram-assistant-users-rl \
    db_name=postgresql \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT ALL PRIVILEGES ON SCHEMA public TO \"{{name}}\"; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";" \
    revocation_statements="REVOKE ALL PRIVILEGES ON SCHEMA public FROM \"{{name}}\"; REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM \"{{name}}\"; DROP ROLE \"{{name}}\";" \
    default_ttl="24h" \
    max_ttl="72h"
# End of snippet
