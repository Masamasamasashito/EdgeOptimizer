# Edge Analyzer Looker Studio ダッシュボード設計

## 1. データソース構成

### Google Sheets CSV（自動更新）
- **更新頻度**: 各 HTTP リクエスト完了時即時アップロード
- **カラム構造**（Flat JSON のキー名ベース）:
  - `headers.general.request-url` - 元のリクエスト URL（完全な URL）
  - `eo.meta.urltype` - URL パターン（画像/JS/CSS など）
  - `eo.meta.duration-ms` - 全リクエスト時間
  - `eo.meta.ttfb-ms` - TTFB (Time To First Byte)
  - `eo.meta.cdn-cache-status` - キャッシュ状態（HIT/MISS）
  - `eo.meta.cdn-header-name` - CDN 検出ヘッダー名
  - `eo.meta.status-code` - HTTP ステータスコード
  - `eo.meta.re-area` - リクエスト発生源（地域）
  - ...など

---

## 2. 計算フィールド定義

### CDN 銘柄識別（必須）
```sql
CASE
  WHEN CONTAINS(eo.meta.cdn-header-name, "cf-ray") THEN "Cloudflare"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-amz-cf-id") THEN "AWS CloudFront"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-nitro") THEN "NitroCDN"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-rl-") THEN "RabbitLoader"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-azure-") THEN "Azure Front Door"
  WHEN (CONTAINS(eo.meta.cdn-header-name, "akamai") OR
        CONTAINS(eo.meta.cdn-header-name, "x-serial") OR
        CONTAINS(eo.meta.cdn-header-name, "x-check-cacheable")) THEN "Akamai"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-vercel-") THEN "Vercel"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-webaccel") THEN "Sakura Internet"
  WHEN (CONTAINS(eo.meta.cdn-header-name, "cdn-pullzone") OR
        CONTAINS(eo.meta.cdn-header-name, "cdn-uid")) THEN "Bunny CDN"
  WHEN (CONTAINS(eo.meta.cdn-header-name, "eagleid") OR
        CONTAINS(eo.meta.cdn-header-name, "x-swift-")) THEN "Alibaba Cloud CDN"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-cnc-") THEN "CDNetworks"
  WHEN (CONTAINS(eo.meta.cdn-header-name, "x-pull") OR
        CONTAINS(eo.meta.cdn-header-name, "x-edge-location")) THEN "KeyCDN"
  WHEN CONTAINS(eo.meta.cdn-header-name, "x-fastly-") THEN "Fastly"
  WHEN (CONTAINS(eo.meta.cdn-header-name, "server") AND
        CONTAINS(eo.meta.cdn-header-value, "google")) THEN "GCP CDN"
  WHEN CONTAINS(eo.meta.cdn-header-name, "cdn_cache_status") THEN "GCP CDN (custom)"
  WHEN CONTAINS(eo.meta.cdn-header-name, "via") THEN "Azure Front Door (via)"
  ELSE COALESCE(eo.meta.cdn-header-name, "Unknown/No CDN")
END
```

---

## 3. ダッシュボード構成（4 ページ）

### Page 1: 「全体性能サマリー」
| コントロール | 仕様 |
|------------|------|
| **KPI カード** | AVG(TTFB)、AVG(Duration)、リクエスト総数、エラー率 |
| **フィルタ** | 日付範囲、CDN 銘柄、地域、URL タイプ |
| **TTFB 推移** | 折れ線（time_created を X） |
| **CDN 別リクエスト分布** | ドーナツチャート（CDN 銘柄 × COUNT） |

---

### Page 2: 「CDN パフォーマンス比較」
| コントロール | 仕様 |
|------------|------|
| **CDN 別 TTFB 平均** | バーチャート（CDN 銘柄 × AVG(TTFB)） |
| **CDN 別キャッシュ効率** | スコアカード（HIT/MISS %、SUMIFS で集計） |
| **TTFB × キャッシュ状態** | ヒートマップ（行：URL タイプ、列：cdn-cache-status、色：AVG(TTFB)） |
| **地域別 CDN 性能** | マルチディメンション表（re-area × cdn-brand × AVG(TTFB)） |

---

### Page 3: 「キャッシュ解析」
| コントロール | 仕様 |
|------------|------|
| **HIT/MISS 分布** | バーチャート（cdn-cache-status × COUNT） |
| **URL タイプ別キャッシュ効率** | ヒートマップ（行：urltype、列：cdn-brand、色：AVG(TTFB HIT 時) / AVG(TTFB MISS 時)） |
| **キャッシュ改善ポテンシャル** | 計算フィールドで「HIT の方が速い程度」を表示 |

---

### Page 4: 「詳細テーブル（ドリルダウン）」
- すべてのカラムを含むフィルタ付き表
- 行ごとに URL、地域、CDN、TTFB、キャッシュ状態を確認可能
- CDN 銘柄の列にソート＆フィルタ設定

---

## 4. フィルタ共通化

| フィルタ名 | 適用範囲 | ソースカラム |
|-----------|---------|-------------|
| 日付範囲 | 全ページ | `time_created` |
| CDN 銘柄 | 全ページ | 計算フィールド（上記） |
| 地域 | 全ページ | `eo.meta.re-area` |
| URL タイプ | 全ページ | `eo.meta.urltype` |

---

## 5. 出力の活用シーン

- **CDN 選択判断**: CDN 別 TTFB、キャッシュ効率比較
- **最適化優先度**: キャッシュ未ヒットかつ低速な URL 特定
- **地域別性能**: 発生源別のパフォーマンス差分析
- **キャパシティ計測**: HTTP リクエスト数・エラー率の把握

---

## 6. headers.general.request-url の活用方法

- **詳細テーブル**: 各リクエストの完全 URL を表示
- **ドリルダウン**: チャートからクリックして特定 URL の詳細確認
- **URL パターン分析**: `eo.meta.urltype` と組み合わせ、どの URL がどのパターンに分類されたか検証
