# Edge Optimizer : Multi Cloud Serverless Request

# Quick Start

Pls create work directory.

EX)
```
mkdir ~/work/docker | cd
```

## 1. git clone
```
git clone https://github.com/Masamasamasashito/EdgeOptimizer.git
```

## 2. Get Ready EO_Infra_Docker/.env

All Docker Compose related files (docker-compose.yml, env.example, caddy/Caddyfile, and service-specific Dockerfiles) are located in the `EO_Infra_Docker` directory.

```
cd EdgeOptimizer/EO_Infra_Docker
cp env.example .env
```

## 3. Generate security keys on EO_Infra_Docker/.env (Crucial step!)

Run the command below for your OS in your terminal to append secrets to `EO_Infra_Docker/.env` (You only need to do this once)

**Note:** Make sure you are in the `EO_Infra_Docker` directory or adjust the paths accordingly.

🍎 macOS / 🐧 Linux (Copy & Paste into Terminal)
```
cd EO_Infra_Docker
echo "" >> .env
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)" >> .env
echo "N8N_EO_REQUEST_SECRET=$(openssl rand -hex 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=')" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=')" >> .env
echo "SEARXNG_CONTAINER_SECRET=$(openssl rand -hex 32)" >> .env
```

🪟 Windows PowerShell (Copy & Paste into PowerShell)
```
cd EO_Infra_Docker
"" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $hex = -join ($bytes | ForEach-Object { $_.ToString("x2") }); "N8N_ENCRYPTION_KEY=$hex" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $hex = -join ($bytes | ForEach-Object { $_.ToString("x2") }); "N8N_EO_REQUEST_SECRET=$hex" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $base64 = [Convert]::ToBase64String($bytes) -replace '[\/+=]', ''; "POSTGRES_PASSWORD=$base64" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $base64 = [Convert]::ToBase64String($bytes) -replace '[\/+=]', ''; "REDIS_PASSWORD=$base64" | Add-Content .env
$bytes = New-Object byte[] 32; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes); $hex = -join ($bytes | ForEach-Object { $_.ToString("x2") }); "SEARXNG_CONTAINER_SECRET=$hex" | Add-Content .env
```

## 4. Environment Variable Access in n8n Workflows

**Important**: To use environment variables (e.g., `{{ $env.N8N_EO_REQUEST_SECRET }}`) in n8n workflows, you need to configure environment variable access permissions.

### Configuration

#### 1. Set Environment Variable in `EO_Infra_Docker/.env` File

The `N8N_EO_REQUEST_SECRET` value must be set in `EO_Infra_Docker/.env` file. This is automatically generated when you run the commands in **Section 3** above. If you need to set it manually, add the following line to your `EO_Infra_Docker/.env` file:

```
N8N_EO_REQUEST_SECRET=your_secret_value_here
```

#### 2. Docker Compose Configuration

The `EO_Infra_Docker/docker-compose.yml` file includes the following settings:

```yaml
N8N_EO_REQUEST_SECRET: ${N8N_EO_REQUEST_SECRET}
N8N_BLOCK_ENV_ACCESS_IN_NODE: false
```

- **`N8N_EO_REQUEST_SECRET: ${N8N_EO_REQUEST_SECRET}`**: This reads the value from the `EO_Infra_Docker/.env` file (set in step 1) and passes it to the n8n container as an environment variable. It can then be accessed in workflows using `{{ $env.N8N_EO_REQUEST_SECRET }}`.
- **`N8N_BLOCK_ENV_ACCESS_IN_NODE: false`**: This setting allows workflows to access environment variables. Setting it to `true` would block access to all environment variables from expressions and Code nodes.

### Important Notes

- **Preview Limitation**: When previewing expressions in the n8n UI (manual execution), you may see an "access to env vars denied" error. This is a known limitation and can be ignored. Environment variables work correctly during actual workflow execution (automated runs).
- **Reference**: For more details, see:
  - [n8n Official Documentation: Environment Variables Security](https://docs.n8n.io/hosting/configuration/environment-variables/security/)
  - [n8n Community Discussion: No access to $env](https://community.n8n.io/t/no-access-to-env/20665)

### Usage in Workflows

In your n8n workflows (e.g., the "170 n8n RequestSecret Token Generator" node), you can access environment variables using:

```
{{ $json.url }}{{ $env.N8N_EO_REQUEST_SECRET }}
```

This is required for the Request Engine token generation process.

## 5. Start Containers

Navigate to the `EO_Infra_Docker` directory and start the containers:

```
cd EO_Infra_Docker
docker compose up -d
```

> [!TIP]
> **Running Multiple Instances / Avoiding Port Conflicts**
> By default, ports are bound to `127.0.0.1` (localhost) to ensure security and reduce port conflicts on your host machine.
> You can customize this behavior or the specific ports used by editing the `EO_Infra_Docker/.env` file (e.g., `DOCKER_HOST_BIND_ADDR`, `DOCKER_HOST_PORT_N8N_CONTAINER`).
>
> **⚠️ CRITICAL: Running Multiple Local Environments**
> If you want to run multiple environments on the same machine:
> 1. **Change ALL VOLUME NAMES** in `EO_Infra_Docker/.env` (e.g., add `_v2` suffix) to prevent data collision
> 2. **Change `DOCKER_HOST_BIND_ADDR`** to a different IP (e.g., `127.0.0.2`, `127.0.0.3`) to avoid port binding conflicts
> 3. **Update `N8N_WEBHOOK_URL`** to match the new IP address
> 
> **WARNING**: If you skip changing volume names, multiple environments will share the SAME volumes, causing data corruption, loss, or overwriting. One environment's data may be completely lost when the other is stopped/removed.
> 
> See `EO_Infra_Docker/env.example` for detailed instructions in the "ADVANCED: Running Multiple Local Environments" section.

### Production Setup (with Caddy)
To start with Caddy (Reverse Proxy), use the `prod` profile.
*Ensure `PRODUCTION=true` and valid domain/email settings in `EO_Infra_Docker/.env` if enabling secure cookies/SSL.*

```
cd EO_Infra_Docker
docker compose --profile prod up -d
```

## 6. n8n Launch Check(local self-hosted)

open : [http://localhost:5678](http://localhost:5678)

# 【Recommended to try】n8n Queue Mode Test

we recommend using the n8n Queue Mode Test as a measure to prevent memory exhaustion in n8n.
[n8nQueueModeTest](n8nQueueModeTest)

# 7. Setup Request Engine

Request Engine is an essential component running on Serverless Computing, designed for purposes such as cache performance verification from edge locations, cache warmup, and security checks.

👉 See detailed setup guide here:
- RequestEngine\RE_README.md
- RequestEngine\aws_lambda\apne1\LAMBDA_README.md
- RequestEngine\aws_lambda\CFn\LAMBDA_CFN_README.md
- RequestEngine\azure_functions\jpeast\AZFUNC_README.md
- RequestEngine\cloudflare_workers\global\CFWORKER_README.md
- RequestEngine\gcp_cloudrun\ane1\RUN_README.md


