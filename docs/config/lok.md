<!-- AUTO-GENERATED — do not edit. Source: https://github.com/arkitektio/lok-server-next/blob/next/CONFIG.md. Run scripts/sync_config_docs.py to update. -->

# Lok — Configuration Reference

This document explains how the **lok** service is configured, then lists every
configuration value, its environment-variable name, its default, and what it does.

Lok is the central authentication / identity provider: it issues OIDC/OAuth2 tokens,
provisions users, organizations and clients, and publishes the verifying keys other
Arkitekt services trust. Its configuration is therefore the richest in the deployment.

The single source of truth for the schema is
[`lok_server/configuration.py`](https://github.com/arkitektio/lok-server-next/blob/next/lok_server/configuration.py); this file documents it for
humans. If the two ever disagree, the code wins — and you can always print the live,
resolved configuration with `python manage.py validate_settings` (see below).

---

## How configuration works

Configuration is a typed [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
schema. Values are resolved from several sources, **highest precedence first**:

1. **Init kwargs** — values passed directly in code (rarely used; tests).
2. **Environment variables** — override anything in the YAML file.
3. **The YAML file** — [`config.yaml`](https://github.com/arkitektio/lok-server-next/blob/next/config.yaml) by default.
4. **File secrets** — Docker/systemd secret files, if used.

So an environment variable always beats the YAML file, which makes containerized
overrides easy without editing the mounted config.

### The YAML file

By default the service reads `config.yaml` next to the project. Point it elsewhere with
the `ARKITEKT_CONFIG_FILE` environment variable:

```bash
ARKITEKT_CONFIG_FILE=/etc/lok/config.yaml python manage.py runserver
```

The file is a nested mapping, one top-level key per configuration *block*:

```yaml
django:
  secret_key: "change-me"
  debug: false
postgres:
  db_name: lok
  username: lok
  password: "change-me"
  host: db
  port: 5432
redis:
  host: redis
  port: 6379
```

### Environment variables (the `__` rule)

Every value is also settable from the environment. The nesting is expressed with a
**double-underscore** (`__`) delimiter, and names are case-insensitive:

| YAML path | Environment variable |
|---|---|
| `postgres.password` | `POSTGRES__PASSWORD` |
| `postgres.port` | `POSTGRES__PORT` |
| `django.debug` | `DJANGO__DEBUG` |
| `redis.channel_prefix` | `REDIS__CHANNEL_PREFIX` |
| `private_key` (top-level) | `PRIVATE_KEY` |
| `oidc_issuer` (top-level) | `OIDC_ISSUER` |

Lists and nested objects (e.g. `authentikate.issuers`, `openid_apps`, `users`,
`organizations`) are awkward to express as environment variables — prefer the YAML file
for those and use env vars for the flat scalars (hosts, ports, passwords, toggles).

### Secrets fail fast

Fields marked **secret / required** below have **no default**. If they are missing from
both the YAML file and the environment, the service refuses to start and raises a
`pydantic.ValidationError` naming the missing field. The same error blocks
`manage.py` entirely, so a broken config cannot be deployed silently.

### Validating a configuration

Run the bundled command to load the config exactly as the app would, validate it, and
print the fully-resolved result as a tree with **secrets redacted**:

```bash
python manage.py validate_settings
```

- Valid config → prints a green `Configuration valid` tree and exits `0`.
- Invalid config → prints each offending field and its error, and exits `1`.

It honors `ARKITEKT_CONFIG_FILE`, so you can validate an alternate file the same way.
(Note: because Django loads settings on startup, a fundamentally invalid config also
surfaces the same validation errors when running *any* `manage.py` command.)

---

## Configuration reference

Secret fields are flagged with 🔒. "Required" means there is no default.

### `django` — core Django framework settings

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `secret_key` 🔒 | `DJANGO__SECRET_KEY` | str | **required** | Django `SECRET_KEY` for cryptographic signing. |
| `debug` | `DJANGO__DEBUG` | bool | `false` | Enable Django debug mode. Never enable in production. |
| `hosts` | `DJANGO__HOSTS` | list[str] | `["*"]` | `ALLOWED_HOSTS` entries. |
| `use_x_forwarded_host` | `DJANGO__USE_X_FORWARDED_HOST` | bool | `true` | Trust the `X-Forwarded-Host` header behind a reverse proxy. |
| `secure_proxy_ssl_header` | `DJANGO__SECURE_PROXY_SSL_HEADER` | bool | `true` | Trust `X-Forwarded-Proto` to detect HTTPS behind a reverse proxy (`SECURE_PROXY_SSL_HEADER`). Disable when not behind a TLS-terminating proxy. |
| `admin` | `DJANGO__ADMIN__*` | object | **required** | Superuser provisioned on first boot (see below). |
| `csrf_trusted_origins` | `DJANGO__CSRF_TRUSTED_ORIGINS` | list[str] | `["http://localhost", "https://localhost"]` | `CSRF_TRUSTED_ORIGINS` for unsafe (POST) requests. |
| `force_script_name` | `DJANGO__FORCE_SCRIPT_NAME` | str | `""` | URL path prefix this service is served under (`FORCE_SCRIPT_NAME`). |
| `language_code` | `DJANGO__LANGUAGE_CODE` | str | `en-us` | Django `LANGUAGE_CODE`. |
| `time_zone` | `DJANGO__TIME_ZONE` | str | `UTC` | Django `TIME_ZONE`. |
| `log_level` | `DJANGO__LOG_LEVEL` | str | `INFO` | Root logger level (e.g. `DEBUG`, `INFO`, `WARNING`). |

#### `django.admin` — superuser created on first boot

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `username` | `DJANGO__ADMIN__USERNAME` | str | **required** | Superuser login name. |
| `password` 🔒 | `DJANGO__ADMIN__PASSWORD` | str | **required** | Superuser password. |
| `email` | `DJANGO__ADMIN__EMAIL` | str | `null` | Superuser email address. |

### `postgres` — PostgreSQL database (Django `DATABASES['default']`)

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `engine` | `POSTGRES__ENGINE` | str | `django.db.backends.postgresql` | Django database backend. |
| `db_name` | `POSTGRES__DB_NAME` | str | **required** | Database name. |
| `username` | `POSTGRES__USERNAME` | str | **required** | Database user. |
| `password` 🔒 | `POSTGRES__PASSWORD` | str | **required** | Database password. |
| `host` | `POSTGRES__HOST` | str | **required** | Database host. |
| `port` | `POSTGRES__PORT` | int | `5432` | Database port. |

### `redis` — Redis connection (channel layer / cache)

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `host` | `REDIS__HOST` | str | **required** | Redis host. |
| `port` | `REDIS__PORT` | int | `6379` | Redis port. |
| `channel_prefix` | `REDIS__CHANNEL_PREFIX` | str | `lok` | Key prefix for the `channels_redis` channel layer. |

### `authentikate` — inbound token verification

Configures how incoming JWT access tokens are verified (the shared `authentikate`
library). Even though lok *issues* tokens, it must also *verify* the tokens presented
to its own API, so it lists itself as a trusted issuer. At least one issuer is required.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `issuers` | — (use YAML) | list[issuer] | **required** | Trusted token issuers whose keys verify incoming tokens (see issuer kinds below). |
| `authorization_headers` | `AUTHENTIKATE__AUTHORIZATION_HEADERS` | list[str] | `["Authorization", "X-Authorization", "AUTHORIZATION", "authorization"]` | Request headers searched (in order) for a Bearer token. |
| `static_tokens` | — (use YAML) | map | `{}` | Pre-defined tokens that bypass signature verification. **Tests only.** |

Each entry in `issuers` is discriminated by its `kind`:

- `kind: rsa` — inline PEM/SSH RSA public key. Fields: `iss`, `kid` (alias of `key_id`, default `1`), `public_key`.
- `kind: rsa_file` — RSA public key read from a PEM file. Fields: `iss`, `kid`, `public_key_pem_file`.
- `kind: jwks_dict` — inline JWKS document. Fields: `iss`, `jwks` (a dict with a `keys` list).
- `kind: jwks_uri` — JWKS fetched from a remote endpoint. Fields: `iss`, `jwks_uri`.

```yaml
authentikate:
  issuers:
    - kind: rsa
      iss: lok
      kid: lok-key-1
      public_key: "ssh-rsa AAAA..."
  static_tokens: {}
```

### `lok` — issuer key material exposed by this service

Lok's own identity-provider key material (separate from the OIDC signing `private_key`
top-level field). Optional; defaults to an empty block.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `public_key` | `LOK__PUBLIC_KEY` | str (SSH/PEM) | `null` | Lok public key used to verify issued tokens. |
| `static_tokens` | — (use YAML) | map | `{}` | Pre-shared static tokens. **Tests only.** |

### `datalayer` — S3 storage and buckets

S3 connection and bucket bindings for the datalayer module (replaces the old top-level
`s3` block). `access_key`, `secret_key` and the `media` bucket are required.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `access_key` 🔒 | `DATALAYER__ACCESS_KEY` | str | **required** | S3 access key. |
| `secret_key` 🔒 | `DATALAYER__SECRET_KEY` | str | **required** | S3 secret key. |
| `host` | `DATALAYER__HOST` | str | `null` | S3 endpoint host. |
| `port` | `DATALAYER__PORT` | int | `null` | S3 endpoint port. |
| `protocol` | `DATALAYER__PROTOCOL` | str | `http` | S3 endpoint protocol (`http` or `https`). |
| `region` | `DATALAYER__REGION` | str | `us-east-1` | S3 region name. |
| `default_acl` | `DATALAYER__DEFAULT_ACL` | str | `private` | Default ACL applied to stored objects (`AWS_DEFAULT_ACL`). |
| `querystring_expire` | `DATALAYER__QUERYSTRING_EXPIRE` | int | `3600` | Presigned URL lifetime in seconds (`AWS_QUERYSTRING_EXPIRE`). |
| `file_overwrite` | `DATALAYER__FILE_OVERWRITE` | bool | `false` | Overwrite existing files on name collision (`AWS_S3_FILE_OVERWRITE`). |
| `secure` | `DATALAYER__SECURE` | bool | `null` | Use TLS for S3. When `null`, derived from `protocol == 'https'`. |
| `media` | — (use YAML) | object | **required** | Bucket for media / general file storage. Each bucket binding is `{ bucket: <name> }`. |
| `zarr` | — (use YAML) | object | `null` | Bucket for Zarr arrays. |
| `parquet` | — (use YAML) | object | `null` | Bucket for Parquet tables. |
| `bigfile` | — (use YAML) | object | `null` | Bucket for large binary files. |

### `account` — django-allauth account / MFA behavior

Controls login, email verification and multi-factor behavior of the bundled
django-allauth flows. All optional with sensible defaults.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `email_verification` | `ACCOUNT__EMAIL_VERIFICATION` | str | `none` | `ACCOUNT_EMAIL_VERIFICATION` (`none` / `optional` / `mandatory`). |
| `login_by_code_enabled` | `ACCOUNT__LOGIN_BY_CODE_ENABLED` | bool | `true` | Enable login by emailed code (`ACCOUNT_LOGIN_BY_CODE_ENABLED`). |
| `mfa_trust_enabled` | `ACCOUNT__MFA_TRUST_ENABLED` | bool | `true` | Allow trusted devices (`MFA_TRUST_ENABLED`). |
| `headless_frontend_urls` | `ACCOUNT__HEADLESS_FRONTEND_URLS__*` | object | see below | SPA URLs for allauth-headless flows. |
| `social_provider_apps` | — (use YAML) | list[str] | `["allauth.socialaccount.providers.orcid", "allauth.socialaccount.providers.google"]` | allauth social provider apps appended to `INSTALLED_APPS`. |

#### `account.headless_frontend_urls` — SPA URLs allauth-headless points users at

The `{key}` placeholders are substituted by allauth. Change the host per deployment.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `account_confirm_email` | `ACCOUNT__HEADLESS_FRONTEND_URLS__ACCOUNT_CONFIRM_EMAIL` | str | `http://localhost/account/verify-email/{key}` | Email-verification link. Set per deployment. |
| `account_reset_password_from_key` | `ACCOUNT__HEADLESS_FRONTEND_URLS__ACCOUNT_RESET_PASSWORD_FROM_KEY` | str | `http://localhost/account/password/reset/key/{key}` | Password-reset link. Set per deployment. |
| `account_signup` | `ACCOUNT__HEADLESS_FRONTEND_URLS__ACCOUNT_SIGNUP` | str | `http://localhost/account/signup` | Signup page URL. Set per deployment. |

### `deployment` — human-facing deployment identity

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `name` | `DEPLOYMENT__NAME` | str | `default` | Deployment name. |
| `description` | `DEPLOYMENT__DESCRIPTION` | str | `A Basic Arkitekt Deployment` | Deployment description. |

### `email` — outbound SMTP (optional)

Optional block for outbound email. Omit it entirely to disable email. When present,
`password` is required.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `host` | `EMAIL__HOST` | str | `NOTSET` | SMTP server host. |
| `port` | `EMAIL__PORT` | int | `587` | SMTP server port. |
| `use_tls` | `EMAIL__USE_TLS` | bool | `true` | Use STARTTLS. |
| `user` | `EMAIL__USER` | str | `NOTSET` | SMTP username. |
| `password` 🔒 | `EMAIL__PASSWORD` | str | **required** (when block present) | SMTP password. |
| `email` | `EMAIL__EMAIL` | str | `NOTSET` | Default `From` address. |

### `ionscale` — tailnet coordinator connection (optional)

Optional connection to an [ionscale](https://github.com/jsiebens/ionscale) tailnet
coordinator. Omit the whole block to disable it. When present, `server_url`,
`admin_key` and `coord_url` are required.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `server_url` | `IONSCALE__SERVER_URL` | str | **required** | Ionscale server URL. |
| `admin_key` 🔒 | `IONSCALE__ADMIN_KEY` | str | **required** | Ionscale admin API key. |
| `coord_url` | `IONSCALE__COORD_URL` | str | **required** | Public coordination URL advertised to clients. |
| `repository` | `IONSCALE__REPOSITORY` | str | `null` | Dotted path to an `IonscaleRepo` factory (tests). |
| `eager_init` | `IONSCALE__EAGER_INIT` | bool | `false` | Eagerly initialize the ionscale repo on boot (tests). |

### Top-level OIDC / provisioning fields

These live at the **root** of the config (not inside a block), so their environment
variable is just the upper-cased field name (e.g. `private_key` → `PRIVATE_KEY`). The
list/object fields below are provisioning data applied on boot — express them in YAML.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `private_key` 🔒 | `PRIVATE_KEY` | str (PEM) | **required** | OIDC/OAuth2 RSA private signing key. Lok refuses to start without it. |
| `oidc_issuer` | `OIDC_ISSUER` | str | `http://lok` | OIDC issuer URL advertised by lok. |
| `kontrol_frontend_url` | `KONTROL_FRONTEND_URL` | str | `/` | Frontend URL used for redirects. |
| `socialaccount_providers` | — (use YAML) | map | `{}` | django-allauth social provider config. |
| `organizations` | — (use YAML) | list[object] | `[]` | Organizations ensured on boot. |
| `users` | — (use YAML) | list[object] | `[]` | Users ensured on boot. |
| `memberships` | — (use YAML) | list[object] | `[]` | User/organization memberships ensured on boot. |
| `redeem_tokens` | — (use YAML) | list[object] | `[]` | Redeem tokens provisioned on boot. |
| `kommunity_partners` | — (use YAML) | list[object] | `[]` | Pre-authorized kommunity partner apps. |
| `system_messages` | — (use YAML) | list[object] | `[]` | System messages shown to users. |
| `openid_apps` | — (use YAML) | list[openid_app] | `[]` | OIDC/OAuth2 clients provisioned on boot. |

#### `openid_apps[]` — OIDC/OAuth2 clients provisioned on boot

Each entry provisions an OAuth2 client (see the `ensureopenid` command). Provide the
client(s), secret(s) and redirect URIs **per deployment** — none are created by default.

| Key | Type | Default | Description |
|---|---|---|---|
| `client_name` | str | **required** | Human-readable client name. |
| `client_id` | str | **required** | OAuth2 `client_id`. |
| `client_secret` 🔒 | str | **required** | OAuth2 client secret. Override per deployment. |
| `redirect_uris` | list[str] | `[]` | Allowed OAuth2 redirect URIs. |

---

## Minimal example

```yaml
django:
  secret_key: "REPLACE_ME"
  debug: false
  admin:
    username: admin
    password: "REPLACE_ME"
    email: admin@example.com
postgres:
  db_name: lok
  username: lok
  password: "REPLACE_ME"
  host: db
  port: 5432
redis:
  host: redis
  port: 6379
authentikate:
  issuers:
    - kind: rsa
      iss: lok
      kid: lok-key-1
      public_key: "ssh-rsa AAAA..."
  static_tokens: {}
datalayer:
  access_key: "REPLACE_ME"
  secret_key: "REPLACE_ME"
  host: minio
  port: 9000
  protocol: http
  media:
    bucket: lok-media
private_key: |
  -----BEGIN PRIVATE KEY-----
  ...
  -----END PRIVATE KEY-----
```

Validate it with `python manage.py validate_settings`.
