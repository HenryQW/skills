# System

<a id="endpoint-flush-history"></a>
## Flush History

Request:

    PUT /v1/flush-history

Note that `DELETE` is also supported.

Returns a `202 Accepted` status code for success.

This API endpoint is available since Miniflux v2.0.49.

<a id="endpoint-healthcheck"></a>
## Healthcheck

The healthcheck endpoint is useful for monitoring and load-balancer configuration.

Request:

    GET /healthcheck

Response:

```
OK
```

- Returns a `200 OK` status code when the service is running and the database connectivity is healthy.
- This route takes into consideration the base path.

<a id="endpoint-liveness"></a>
## Liveness

Request:

    GET /liveness

Alternatively:

    GET /healthz

Response:

```
OK
```

- Returns a `200 OK` status code when the service is running.
- This endpoint does not check database connectivity.
- These routes do not take the base path into consideration and are available at the root of the Miniflux instance.
- This endpoint can be used as Kubernetes liveness probe.
- Available since Miniflux 2.2.9.

<a id="endpoint-readiness"></a>
## Readiness

Request:

    GET /readiness

Alternatively:

    GET /readyz

Response:

```
OK
```

- Returns a `200 OK` status code when the service is ready to accept requests.
- This endpoint checks database connectivity.
- These routes do not take the base path into consideration and are available at the root of the Miniflux instance.
- This endpoint can be used as Kubernetes readiness probe.
- Available since Miniflux 2.2.9.

<a id="deprecated-endpoint-version"></a>
## Application version

The version endpoint returns Miniflux build version.

Request:

    GET /version

Response:

```
2.0.22
```

- This API endpoint is available since Miniflux v2.0.22
- It's deprecated since version 2.0.49
- It has been removed in Miniflux v2.2.17

<a id="endpoint-version"></a>
## Application version and build information

The version endpoint returns Miniflux version and build information.

Request:

    GET /v1/version

Response:

```json
{
    "version":"2.0.49",
    "commit":"69779e795",
    "build_date":"2023-10-14T20:12:04-0700",
    "go_version":"go1.21.1",
    "compiler":"gc",
    "arch":"amd64",
    "os":"linux"
}
```

This API endpoint is available since Miniflux v2.0.49.

