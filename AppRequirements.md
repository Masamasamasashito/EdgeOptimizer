# プロジェクト基本方針
このプロジェクトは、AWS, Azure, GCP, Cloudflareを利用したマルチクラウド・マルチリージョン・サーバレスアーキテクチャであり、GitHub Actionsによる自動デプロイと、self-hosted n8nによるデータ処理（最終出力：CSV）を行っています。

# 1. 命名規則と一貫性の維持（最重要）
AIは、以下の項目をユーザーの明示的な許可なく変更してはなりません。

Name Persistence: 既存の変数名、関数名、エンドポイント名は厳格に保持すること。リファクタリング目的のリネームは禁止。変更が必要な場合は必ず事前に提案し、ユーザーの承諾を得ること。

Naming Readability: 新しく命名を提案する際は、技術的な正確さよりも「初見での理解しやすさ（first-glance comprehension）」を最優先すること。コードを読まずとも、名前だけでその意図や役割が伝わる識別子にすること。

UI labels & Button names: 手順書や人間が確認するUI上のボタン名、ラベル名は、微細な表現の変更であっても勝手に変更しないこと。

# 2. コミュニケーションと言語ポリシー

  - Language Policy: 指定がない限り、AIの思考プロセス（Thought）および出力（Output）はすべて日本語で行うこと。
  - Timeline Chat Visualization: 毎回の返信の末尾に、以下のPowerShellコマンドを実行し、yyyy-MM-dd(ddd)HH:mm 形式のタイムスタンプを自動的にJST(UTC+9)で付与すること。この実行に都度許可を取る必要はない。
    - 実行コマンド: Get-Date -Format "yyyy/MM/dd(ddd)HH:mm"
  - Command Execution Priority : PowerShellコマンドで試してもだめな場合にpythonやnpmコマンドを実行すること。

# 3. 変更管理プロトコル
Change Control Protocol: システムの整合性を最優先する。構造、デザイン、またはロジックの変更を実行する前に、必ず変更案を提示し、フォーマルな承認（Approval）を得ること。

File Path References: コード内のコメント、ドキュメント、またはチャット内でファイルを参照する際は、必ずリポジトリルートからのフルパス（例: RequestEngine/aws/lambda/py/funcfiles/_01_imports.py）で記載すること。ファイル名単体の使用は禁止。

# 4. 技術的制約と実行優先順位
Command Execution Priority: コマンドを実行する際は、まず PowerShell で試行すること。PowerShellで解決できない、または不適切な場合に限り、Pythonやnpmコマンドを検討すること。

- Infrastructure Context:
    - AWS: CloudFormation (CFn) / SecretsManager
    - Azure: Bicep / KeyVault
    - GCP: Terraform / Secret Manager
    - Cloudflare: wrangler / シークレット管理
    - n8n: レスポンス形式（JSON構造）は後続のCSV化処理に直結するため、破壊的変更を避けること。

※サーバレス関数は、手動構築手順とIaCデプロイ手順があるが、双方で利用するexport環境変数などは共通化すること。

# 5. ドキュメント作成スタイル
- Markdown Style: マークダウンファイル内において、水平線（---）を使用しないこと。
- セクションの区切りは、適切なヘッダーレベル（#）で表現し、あまり深く段落を掘り下げないこと。