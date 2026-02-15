# Edge Optimizer (EO) Infrastructure Docker の Docker Image 更新

`EO_Infra_Docker\docker-compose.yml`では、各サービスがDockerfileを使用してカスタムイメージ名（`-eo`サフィックス付き）でビルドされています。ベースイメージを更新する場合や、Dockerfileの変更を反映する場合は、以下の手順で古いイメージを削除してから再ビルドしてください。

### 手順

#### 1. コンテナを停止して削除

```bash
docker compose down
```

#### 2. カスタムイメージを削除（-eoサフィックス付きのイメージ）

すべてのEOカスタムイメージを一括削除する場合（接尾辞が `-eo` のイメージのみ）

**注意**: コンテナが稼働中の場合、イメージは削除できません（エラーになります）。そのため、必ず先に `docker compose down` を実行してください。

**Linux / macOS / Git Bash:**
```bash
docker images | grep "-eo:" | awk '{print $1":"$2}' | xargs -r docker rmi
```

**Windows PowerShell:**
```powershell
docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -like "*-eo:*" } | ForEach-Object { docker rmi $_ }
```

**個別に削除する場合（例）:**
```bash
docker rmi n8nio/n8n-eo:latest
docker rmi postgres-eo:alpine
docker rmi redis-eo:alpine
docker rmi docker.io/searxng/searxng-eo:latest
docker rmi caddy-eo:alpine
docker rmi mcr.microsoft.com/playwright-eo:noble
```

#### 3. ベースイメージも更新したい場合（オプション）

**注意**: `docker compose pull`は使用できません。このプロジェクトでは各サービスがDockerfileを使用してカスタムイメージ名（`-eo`サフィックス付き）でビルドされているため、`docker-compose.yml`の`image:`で指定されているのはカスタムイメージ名（例: `n8nio/n8n-eo:latest`）であり、これはDocker Hubなどには存在しません。ベースイメージ（例: `n8nio/n8n:latest`）を更新するには、以下のコマンドで個別にプルする必要があります。

**ワンライナー:**

**Linux / macOS / Git Bash:**
```bash
docker pull n8nio/n8n:latest && docker pull postgres:alpine && docker pull redis:alpine && docker pull docker.io/searxng/searxng:latest && docker pull caddy:alpine && docker pull mcr.microsoft.com/playwright:noble
```

**Windows PowerShell:**
```powershell
docker pull n8nio/n8n:latest; docker pull postgres:alpine; docker pull redis:alpine; docker pull docker.io/searxng/searxng:latest; docker pull caddy:alpine; docker pull mcr.microsoft.com/playwright:noble
```

**個別に実行する場合:**
```bash
docker pull n8nio/n8n:latest
docker pull postgres:alpine
docker pull redis:alpine
docker pull docker.io/searxng/searxng:latest
docker pull caddy:alpine
docker pull mcr.microsoft.com/playwright:noble
```

#### 4. 再ビルドして起動（--buildオプションで強制的に再ビルド）

```bash
docker compose up -d --build
```

### 注意事項

- **コンテナ稼働中のイメージ削除**: コンテナが稼働中の場合、そのコンテナが使用しているイメージは削除できません。`docker rmi`を実行すると「イメージが使用中」というエラーが返されます。そのため、**必ず先に `docker compose down` を実行してコンテナを停止・削除してからイメージを削除してください**。
- **データの保持**: `docker compose down`を実行しても、Docker volumesに保存されているデータ（n8nのワークフロー、PostgreSQLのデータなど）は削除されません。
- **Volumeの引き継ぎ**: Dockerイメージを削除しても、**volumesは独立して管理されているため残ります**。新しいイメージからコンテナを作成する際、`docker-compose.yml`で同じvolume名を指定していれば、**既存のvolumeが自動的にマウントされ、データは引き継がれます**。
  - 例: `n8n_data_docker_volume`に保存されているn8nのワークフローや設定は、イメージを削除して再ビルドしても保持されます。
  - 例: PostgreSQLのデータベース（`postgres_data_docker_volume`）も同様に引き継がれます。
- **イメージ名の確認**: 削除前に、現在のイメージ名を確認するには `docker images` コマンドを使用してください。
- **部分的な更新**: 特定のサービスのみ更新したい場合は、`docker compose build <service_name>` を実行してから `docker compose up -d <service_name>` で再起動できます。
- **Volumeの確認**: 現在のvolumesを確認するには `docker volume ls` コマンドを使用してください。

### なぜこの方法が必要か

`docker-compose.yml`では、各サービスがDockerfileを使用して接尾辞に`-eo`を付けたカスタムイメージ名（例: `n8nio/n8n-eo:latest`）でビルドされています。カスタムイメージである場合、再ビルドをスキップするため、更新するには古いイメージを削除してから再ビルドする必要があります。

