# Configuration

Every Arkitekt service is configured the same way: a typed
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
schema resolved from environment variables, config files and defaults.

Each service publishes a full configuration reference (its `CONFIG.md`).
These pages are **auto-synced** from the individual service repositories by
`scripts/sync_config_docs.py` — edit them upstream, not here.

| Service | Configuration reference | Source repo |
| --- | --- | --- |
| Alpaka | [config/alpaka.md](config/alpaka.md) | [jhnnsrs/alpaka-server](https://github.com/jhnnsrs/alpaka-server) |
| Dokuments | [config/dokuments.md](config/dokuments.md) | [jhnnsrs/dokuments-server](https://github.com/jhnnsrs/dokuments-server) |
| Elektro | [config/elektro.md](config/elektro.md) | [jhnnsrs/elektro-server](https://github.com/jhnnsrs/elektro-server) |
| Example | [config/example.md](config/example.md) | [jhnnsrs/example-server](https://github.com/jhnnsrs/example-server) |
| Fluss | [config/fluss.md](config/fluss.md) | [jhnnsrs/fluss-server-next](https://github.com/jhnnsrs/fluss-server-next) |
| Kabinet | [config/kabinet.md](config/kabinet.md) | [arkitektio/kabinet-server](https://github.com/arkitektio/kabinet-server) |
| Kraph | [config/kraph.md](config/kraph.md) | [jhnnsrs/kraph-server](https://github.com/jhnnsrs/kraph-server) |
| Lok | [config/lok.md](config/lok.md) | [arkitektio/lok-server-next](https://github.com/arkitektio/lok-server-next) |
| Lovekit | [config/lovekit.md](config/lovekit.md) | [jhnnsrs/lovekit-server](https://github.com/jhnnsrs/lovekit-server) |
| Mikro | [config/mikro.md](config/mikro.md) | [arkitektio/mikro-server-next](https://github.com/arkitektio/mikro-server-next) |
| Omero-Ark | [config/omero-ark-server.md](config/omero-ark-server.md) | [arkitektio/omero-ark-server](https://github.com/arkitektio/omero-ark-server) |
| Rekuest | [config/rekuest.md](config/rekuest.md) | [jhnnsrs/rekuest-server-next](https://github.com/jhnnsrs/rekuest-server-next) |
