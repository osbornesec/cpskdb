# Docker Compose Configuration

## Environment Variables

The project uses environment variables to configure Docker Compose behavior
for different environments.

### Restart Policy Configuration

The Qdrant service restart policy can be configured via the
`QDRANT_RESTART_POLICY` environment variable:

| Environment | Policy | Description |
|-------------|--------|-------------|
| **Local/Dev** | `unless-stopped` (default) | Service restarts automatically unless manually stopped. Good for development where you want persistent services. |
| **CI/Testing** | `on-failure:3` | Service restarts up to 3 times on failure, then stops. Prevents infinite crash loops and surfaces errors quickly in CI. |
| **Production** | `unless-stopped` or `on-failure:5` | Choose based on your operational posture. Use `unless-stopped` for high-availability setups where services are supervised by external process managers (like systemd or a container orchestrator). Use `on-failure:N` when you want crash loops to stop and trigger alerts for manual intervention; choose N based on your tolerance for transient failures. |

### Image Pinning

Pin the QDRANT_IMAGE to avoid drift and ensure reproducible deployments:

**Tagged Pin Example:**
```bash
QDRANT_IMAGE=qdrant/qdrant:1.8.2
```

**Digest Pin Example (Preferred):**
```bash
QDRANT_IMAGE=qdrant/qdrant@sha256:abc123def456...
```

**Note:** Avoid using `latest` in CI/Production to prevent non-reproducible upgrades.

### Usage Examples

#### Local Development

```bash
# Uses default unless-stopped policy
docker compose up -d
```

#### CI/CD Pipeline

```bash
# Set CI-appropriate restart policy
export QDRANT_RESTART_POLICY=on-failure:3
docker compose up -d
```

#### Using Environment Files

Environment files allow you to manage configuration for different environments separately. Docker Compose automatically picks up a `.env` file in the project root.

**Example `.env` file:**
```
# .env
# Local development settings
QDRANT_IMAGE=qdrant/qdrant:latest
QDRANT_RESTART_POLICY=unless-stopped
```

You can also specify a different environment file, which is useful for CI or other environments.

**CI Usage Example:**
```bash
# .env.ci
# CI-specific settings
QDRANT_IMAGE=qdrant/qdrant:1.9.0
QDRANT_RESTART_POLICY=on-failure:3
```

To use the CI-specific file, invoke Docker Compose with the `--env-file` flag:
```bash
docker compose --env-file ./.env.ci up -d
```

### Configuration Files

- `.env.example` - Development defaults and documentation
- `.env.ci` - CI-specific configuration
- `.env` - Local overrides (not tracked in git)

### Benefits

1. **CI Error Detection**: `on-failure:3` policy prevents masking of crash
   loops in CI
2. **Development Convenience**: `unless-stopped` policy keeps services
   running locally
3. **Flexibility**: Easy to adjust behavior per environment without code
   changes
4. **Debugging**: Failed containers stop after limited retries, making logs
   accessible

### Troubleshooting

If you encounter issues with containers restarting:

1. **Check logs**: `docker compose logs qdrant`
2. **Verify environment**: `docker compose config` shows resolved
   configuration
3. **Adjust retry count**: Change `on-failure:3` to `on-failure:1` for faster
   failure detection
4. **Disable restarts**: Set `QDRANT_RESTART_POLICY=no` for debugging
