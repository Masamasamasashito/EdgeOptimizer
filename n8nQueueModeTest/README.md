# n8n Queue Mode Smoke Test (Webhook Processing + Concurrency)

This smoke test uses three n8n workflow JSON files to validate **n8n Queue Mode**
behavior using webhook fan-out and a fixed wait time.

In this document:
- **n8n (main)** refers to the main n8n instance handling the UI and orchestration.
- **n8n-worker** refers to the background worker process executing queued jobs.
(This avoids confusion with Cloudflare Workers.)

---

## Workflows in this bundle

- **n8nQueueModeTest/Queue Mode _ Webhook Processing - Concurrency Testing1.json**  
  Manual trigger → calls Testing2 via webhook (indirect start)

- **n8nQueueModeTest/Queue Mode _ Webhook Processing - Concurrency Testing2.json**  
  Webhook trigger → creates multiple items → triggers Testing3 via webhook

- **n8nQueueModeTest/Queue Mode _ Webhook Processing - Concurrency Testing3.json**  
  Webhook trigger → waits for a fixed duration → responds to the webhook

---

## Run Queue Mode Test in this Repository

To run this test using the provided `EO_Infra_Docker\docker-compose.yml`, you need to enable Queue Mode and start the worker service.

### 1. Configure `EO_Infra_Docker\docker-compose.yml`

Open the `EO_Infra_Docker\docker-compose.yml` file in the parent directory (`EO_Infra_Docker\docker-compose.yml`) and make the following changes:

1.  **Enable Queue Mode for main n8n:**
    In `EO_Infra_Docker\docker-compose.yml`, uncomment line 61 (remove `# `):
    ```yaml
    # In EO_Infra_Docker\docker-compose.yml
    EXECUTIONS_MODE: queue
    ```

2.  **Enable n8n-worker service:**
    In `EO_Infra_Docker\docker-compose.yml`, uncomment the entire `n8n-worker` service block (lines 152–198).
    Ensure the command sets concurrency to 1 (default):
    ```yaml
    # In EO_Infra_Docker\docker-compose.yml service: n8n-worker
    command: ["worker","--concurrency=1"]
    ```

### 2. Start the Services

start the containers:

```bash
docker compose up -d
```

### 3. Verify Worker Status

Check that the worker is running and connected to Redis:

```bash
docker compose logs -f n8n-worker
```

### 4. Setup n8n Account and License

1.  Open the n8n UI (http://localhost:5678).
2.  **Create an n8n user account** (email and password).
3.  **Activate n8n license**:
    - If prompted, sign up for a free license or trial.
    - Check your email for the activation code/link if required.
    - Confirm the instance is activated.

### 5. Execute the Smoke Test

1.  **Import** the 3 JSON workflows from this directory into the n8n UI.
2.  **Publish** "Testing2" and "Testing3" workflows (toggle Active switch to On).
3.  Open "**Testing1**" and click **Execute workflow**.
4.  Observe the executions in the **Executions** tab. You should see "Testing2" triggering multiple "Testing3" instances, which will be processed by the worker.

---

## Prerequisites (General)

- **n8n (main)** is running in **Queue Mode** with **Redis** configured.
- At least one **n8n-worker** process is running  
  (for example: `n8n worker --concurrency=N`).
- These workflows are intended to run **within the same docker-compose environment**,
  so the hostname `n8n` resolves correctly inside the Docker network.

---

## Import the workflows

1. Open the **n8n (main)** UI.
2. Go to **Workflows**.
3. Select **Import from File**.
4. Import the following files:
   - `Queue Mode _ Webhook Processing - Concurrency Testing1.json`
   - `Queue Mode _ Webhook Processing - Concurrency Testing2.json`
   - `Queue Mode _ Webhook Processing - Concurrency Testing3.json`

---

## Publish webhook workflows

1. Open **Testing2**.
2. Click **Publish**.
3. Open **Testing3**.
4. Click **Publish**.

> **Testing1** is manual-only and does not need to be published.

---

## Run the smoke test

1. Open **Testing1** in **n8n (main)**.
2. Click **Execute workflow**.

What happens internally:

- **n8n (main)** receives the manual execution and calls Testing2 via webhook.
- The execution is enqueued in Redis.
- **n8n-worker** picks up the queued jobs.
- Testing2 fans out by triggering Testing3 multiple times.
- Each Testing3 execution waits for a fixed duration, then responds.

---

## Verify Queue Mode behavior

### In the n8n UI (main)

1. Go to **Overview → Executions**.
2. Confirm:
   - Multiple **Testing3** executions start at nearly the same time.
   - Each **Testing3** execution runtime matches the configured wait duration.
   - Overall completion speed depends on **n8n-worker** concurrency.

### In Docker logs (recommended)

Verify that **n8n-worker** is actually consuming queued jobs:

```bash
docker compose logs -f n8n-worker
```
