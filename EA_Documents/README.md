# Edge Analyzer (EA) データ分析・可視化基盤設計（ローカルn8n拡張・超低コスト版）

- Edge Optimizerのマルチリージョン展開で収集された稼働結果を元に、Looker Studioを用いてEdgeの「痛み」を可視化し、キャッシュ最適化によるビジネスインパクトを分析するための基盤設計
- Edge Optimizerのアーキテクチャ（n8nによるオーケストレーションとデータ集約）を活かし、ランニングコストを実質ゼロに抑える「n8n ＋ Google Drive ＋ Looker Studio」** の構成

## 1. 全体アーキテクチャ案（S3完全撤廃・n8nワークフロー拡張モデル）

n8nワークフローの末尾（ノード `#420 JSON to RequestResultsCSV`）で手動ダウンロードしているCSVの蓄積プロセスを、n8n標準ノードを用いてGoogle Drive のスプレッドシートに自動保存する

### データフロー
1. **データ収集 (Edge Optimizerの既存フロー)**
   - ローカル（またはオンプレミス）で稼働するn8nがオーケストレーターとして機能。
   - n8nからAWS Lambda等のRequest Engineへ指示出し。
   - Request Engine はTarget CDN Edgeから応答ヘッダーやTTFB等のパフォーマンス指標を取得し、JSON形式でn8nに返却。

2. **データ変換・蓄積 (ローカル n8n のワークフロー拡張)**
   - n8nが全リージョンからのJSONを結合・フラット化（ノード `#350 JSON Flattener`付近）。
   - 事前準備: n8nのGoogle Driveノードを使うために、Google Cloud Consoleでサービスアカウントを作成し、Google Drive APIとGoogle Sheets APIを有効化。サービスアカウントキー（JSON）を発行またはOAuth2認証の準備。
   - **【新規追加】** ここで生成されたデータを直接、n8nの `Google Drive` ノードまたは `Google Sheets` ノードへ渡します。
     - **パターンA（Sheet直結）:** 解析に必要なメトリクス（TTFB、cache-status等）に絞り込み、マスターとなるGoogleスプレッドシートの最下行へ`Append`（追記）し続ける。
     - **パターンB（CSV保存）:** 生成したCSVファイルをそのままGoogle Driveの特定フォルダへ定期的に自動アップロードする。

3. **データウェアハウス (Google Drive / Google Sheets)**
   - 追加のDBやBigQueryを契約することなく、Google Drive上のスプレッドシート（またはCSV群）が無料のデータウェアハウスとして機能します。

4. **BIツール (Looker Studio)**
   - 無償の **Google Sheetsコネクタ**（またはGoogle Driveコネクタ）を利用してLooker Studioに接続。
   - n8nから自動で追記されたデータを元に、リアルタイムに近いダッシュボードを描画します。

---

## 2. データスキーマと主要な分析軸 (KPIs)

蓄積データ（`RequestResults_YYYY-MM-DD_HH_mm.csv` のフォーマット）を活用し、以下の軸で分析を行います。

### 活用する主要データカラム
- **時間・地理**: `eo.meta.request-start-timestamp` (パースして時系列軸に), `eo.meta.re-area` (リージョン比較用)
- **パフォーマンス**: `eo.meta.ttfb-ms` (TTFBの中央値や95パーセンタイル), `eo.meta.duration-ms`
- **キャッシュ状況**: `eo.meta.cdn-cache-status` (HIT/MISS), `eo.re.eviction-alert` (EVICTED / FRESH)
- **コンテンツ情報**: `eo.meta.urltype` (main_document, asset)

### Looker Studio ダッシュボードの切り口案

#### A. 「Edge AI」や「ECサイトのCDN Edge」への痛みの可視化
- **Edge AIの推論レイテンシとコールドスタート（TTFB）:**
  - AIの応答速度において `eo.meta.ttfb-ms` は「ネットワーク遅延＋EdgeでのAI推論時間」を意味します。ここがスパイク（急増）している場合、EdgeノードでのAIモデルのコールドスタートやリソース枯渇の「痛み」が発生していることが可視化できます。
- **Edge Eviction (キャッシュ剥がれ) の検知 (ECサイト等に有効):**
  - `eo.re.eviction-alert` で `⚠️ EVICTED: Cache Lost` をカウント。
  - キャッシュが本来保持されるべきコンテンツが、Edgeの容量都合で頻繁に剥がされている実態（Edgeの痛み）を可視化。
- **特定リージョンでの高負荷やエラー検知:**
  - `re-area` 別の `headers.general.status-code` (5xxエラー等) や `duration-ms` を監視し、特定のクラウド・特定の地域のEdge AIコンピュートリソースがパンクしていないかを時系列で表示。
  - ※ *AI特有のヘッダー（例: `Server-Timing`, `x-ratelimit-remaining`, トークン消費量など）を取得したくなった場合でも、EOには `extensions`（拡張機能 `_ext_*.py`）の仕組みがあるため、コアロジックを改修せずに後から容易に追加・収集可能です。*

#### B. Edge Optimizer 導入による継続的効果（BEFORE / AFTER）
- **パフォーマンス差分の可視化:**
  - `cdn-cache-status = HIT` (または `FRESH`) が維持されている間の平均 `ttfb-ms` と、`MISS` 時の平均 `ttfb-ms` の差分を比較。
- **機会損失の解消 (利益への換算):**
  - Looker Studioの計算フィールドを活用。
  - 【例】 `(MISS時のTTFB - HIT時のTTFB) × トラフィック推定数 × CVR低下係数 × 客単価`
  - 「Edge Optimizerによって月間推計 ◯◯ ミリ秒のレイテンシを削減 → ◯◯ 円の売上（利益）向上」といった金額換算のKPIダッシュボードを構築。

---

## 3. 今後の具体的な構築ステップ（EA開発フェーズ）

現在のEdge Optimizer（EO）の資産をそのまま活用し、Edge Analyzer（EA）へシームレスに繋ぎます。

1. **Google Cloud / Workspace 側の準備:**
   - GCPプロジェクトで `Google Drive API` および `Google Sheets API` を有効化。
   - サービスアカウントキー（JSON）を発行またはOAuth2認証の準備。
   - 保存先となるGoogleスプレッドシートを作成し、サービスアカウントに編集権限を付与。

2. **n8n ワークフローの拡張 (EO側のアップデート):**
   - 既存の `eo-n8n-workflow-jp.json` をベースに更新。
   - `420 JSON to RequestResultsCSV` ノードの後に、**Google Sheets または Google Drive ノード** を追加設定。
   - 定期実行（Cronトリガー等）で自動的にWarmupが走り、その結果が毎回Google Sheetsに `Append` される一連のループを完成させる。

3. **Looker Studio モデリング (EA側のコア開発):**
   - Looker Studioを開き、対象のGoogle Sheetsに接続（データソース化）。
   - 計算フィールドや各種グラフ（折れ線グラフ、ヒートマップ、スコアカード）を配置。
   - レポートをデザインし、関係者へ共有できる分析基盤（ダッシュボード）を完成させる。

この構成により、Request Engine (Lambda等) の変更やS3バケット等の追加AWSリソースを一切必要とせず、手元のn8nで加工・集約したデータを直接Googleエコシステムへ流し込む、最強のコストパフォーマンスを誇る分析体制が整います。
