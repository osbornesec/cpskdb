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
| **Production** | `unless-stopped` or `on-failure:5` | Choose based on requirements. `unless-stopped` for high availability, `on-failure:N` for controlled failure handling. |

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

```bash
# For CI
docker compose --env-file .env.ci up -d

# For local development
docker compose --env-file .env.example up -d
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