<!-- AUTO-GENERATED — do not edit. Source: https://github.com/jhnnsrs/kraph-server/blob/next/CONFIG.md. Run scripts/sync_config_docs.py to update. -->

# Kraph — Configuration Reference

This document explains how the **kraph** service is configured, then lists every
configuration value, its environment-variable name, its default, and what it does.

The single source of truth for the schema is
[`kraph_server/configuration.py`](https://github.com/jhnnsrs/kraph-server/blob/next/kraph_server/configuration.py); this file documents it for
humans. If the two ever disagree, the code wins — and you can always print the live,
resolved configuration with `python manage.py validate_settings` (see below).

---

## How configuration works

Configuration is a typed [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
schema. Values are resolved from several sources, **highest precedence first**:

1. **Init kwargs** — values passed directly in code (rarely used; tests).
2. **Environment variables** — override anything in the YAML file.
3. **The YAML file** — [`config.yaml`](https://github.com/jhnnsrs/kraph-server/blob/next/config.yaml) by default.
4. **File secrets** — Docker/systemd secret files, if used.

So an environment variable always beats the YAML file, which makes containerized
overrides easy without editing the mounted config.

### The YAML file

By default the service reads `config.yaml` next to the project. Point it elsewhere with
the `ARKITEKT_CONFIG_FILE` environment variable:

```bash
ARKITEKT_CONFIG_FILE=/etc/kraph/config.yaml python manage.py runserver
```

The file is a nested mapping, one top-level key per configuration *block*:

```yaml
django:
  secret_key: "change-me"
  debug: false
postgres:
  db_name: kraph_db
  username: kraph
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
| `datalayer.region` | `DATALAYER__REGION` |

Lists and nested objects (e.g. `authentikate.issuers`) are awkward to express as
environment variables — prefer the YAML file for those and use env vars for the flat
scalars (hosts, ports, passwords, toggles).

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
| `admin` | `DJANGO__ADMIN__*` | object | `null` | Superuser provisioned on first boot (see below). |
| `csrf_trusted_origins` | `DJANGO__CSRF_TRUSTED_ORIGINS` | list[str] | `["http://localhost", "https://localhost"]` | `CSRF_TRUSTED_ORIGINS` for unsafe (POST) requests. |
| `force_script_name` | `DJANGO__FORCE_SCRIPT_NAME` | str | `""` | URL path prefix this service is served under (`FORCE_SCRIPT_NAME`). |

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

### `authentikate` — inbound token verification

Configures how incoming JWT access tokens are verified (the shared `authentikate`
library). At least one issuer is required.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `issuers` | — (use YAML) | list[issuer] | **required** | Trusted token issuers whose keys verify incoming tokens (see issuer kinds below). |
| `authorization_headers` | `AUTHENTIKATE__AUTHORIZATION_HEADERS` | list[str] | `["Authorization", "X-Authorization", "AUTHORIZATION", "authorization"]` | Request headers searched (in order) for a Bearer token. |
| `provenance_header` | `AUTHENTIKATE__PROVENANCE_HEADER` | list[str] | rekuest/provenance task header names | Request headers searched for an inbound provenance token. |
| `static_tokens` | — (use YAML) | map | `{}` | Pre-defined tokens that bypass signature verification. **Tests only.** |
| `provenance` | — (use YAML) | object | `null` | Inbound provenance-token verification (separate issuers/`audience`/`algorithms`; `null` disables it). |

Each entry in `issuers` is discriminated by its `kind`:

- `kind: rsa` — inline PEM RSA public key. Fields: `iss`, `kid` (default `1`), `public_key`.
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

### `datalayer` — S3 storage and buckets

S3 storage connection and bucket bindings (the datalayer module; replaces the old
top-level `s3` block). This block is **required** for kraph, and `access_key`,
`secret_key`, and the `media` bucket must be set.

| Key | Env var | Type | Default | Description |
|---|---|---|---|---|
| `access_key` 🔒 | `DATALAYER__ACCESS_KEY` | str | **required** | S3 access key. |
| `secret_key` 🔒 | `DATALAYER__SECRET_KEY` | str | **required** | S3 secret key. |
| `host` | `DATALAYER__HOST` | str | `null` | S3 endpoint host. |
| `port` | `DATALAYER__PORT` | int | `null` | S3 endpoint port. |
| `protocol` | `DATALAYER__PROTOCOL` | str | `http` | S3 endpoint protocol (`http` or `https`). |
| `region` | `DATALAYER__REGION` | str | `us-east-1` | S3 region name. |
| `media` | — (use YAML) | object | **required** | Bucket for media / general file storage, `{ bucket: <name> }`. |
| `zarr` | — (use YAML) | object | `null` | Bucket for Zarr arrays, `{ bucket: <name> }`. |
| `parquet` | — (use YAML) | object | `null` | Bucket for Parquet tables, `{ bucket: <name> }`. |
| `bigfile` | — (use YAML) | object | `null` | Bucket for large binary files, `{ bucket: <name> }`. |

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
  db_name: kraph_db
  username: kraph
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
datalayer:
  access_key: "REPLACE_ME"
  secret_key: "REPLACE_ME"
  host: minio
  port: 9000
  protocol: http
  media:
    bucket: mikromedia
```

Validate it with `python manage.py validate_settings`.
