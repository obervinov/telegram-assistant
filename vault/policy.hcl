# Allowed to look up the approle token
path "auth/token/lookup" {
  capabilities = ["read"]
}

# Allowed to revoke the approle token
path "auth/token/revoke" {
  capabilities = ["update"]
}

# Allowed to look up its own approle token
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# Allowed to connect a mount point and update settings
path "telegram-assistant/config" {
  capabilities = ["update"]
}

# Allowed to list bot configurations
path "telegram-assistant/configuration/*" {
  capabilities = ["read", "list"]
}

# Allowed to read other configurations
path "telegram-assistant/data/configuration/*" {
  capabilities = ["read", "list"]
}

# Allowed to read and generate credentials in database engine
path "telegram-assistant-database/creds/*" {
  capabilities = ["read", "list", "update"]
}
