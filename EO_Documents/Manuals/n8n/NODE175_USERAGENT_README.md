# #175 Assign UserAgents 設定ガイド

実際のユーザーによるリクエストになるべく近づけるため、URLタイプ（`main_document` / `asset`）ごとに適用する User-Agent 一覧を設定します。

## 概要

| 項目 | 説明 |
|-----|------|
| ノード番号 | #175 |
| ノード名 | Assign UserAgents |
| ノードタイプ | Code（JavaScript） |
| 目的 | URLタイプ別にUser-Agentバリアントを展開 |

## 設定箇所

ノード内のCodeで、以下の2つの配列を編集します:

```javascript
// メインドキュメント用 User-Agent 一覧
const mainDocumentUserAgentList = [
  { label: 'ios_safari_17', ua: '...' },
  // ここに追加
];

// アセット用 User-Agent 一覧
const assetUserAgentList = [
  { label: 'ios_safari_17', ua: '...' },
  // ここに追加
];
```

## User-Agent 一覧（コピペ用）

### モバイル（iOS）

| label | User-Agent |
|-------|------------|
| `ios_safari_17` | `Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1` |
| `ios_safari_16` | `Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1` |
| `ios_safari_15` | `Mozilla/5.0 (iPhone; CPU iPhone OS 15_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.6 Mobile/15E148 Safari/604.1` |
| `ipad_safari_17` | `Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1` |

### モバイル（Android）

| label | User-Agent |
|-------|------------|
| `android_chrome_pixel` | `Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36` |
| `android_chrome_galaxy` | `Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36` |
| `android_chrome_pixel8` | `Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36` |
| `android_go` | `Mozilla/5.0 (Linux; Android 12; Android Go) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.60 Mobile Safari/537.36` |
| `android_webview` | `Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36` |

### デスクトップ（Windows）

| label | User-Agent |
|-------|------------|
| `win_chrome_120` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36` |
| `win_chrome_118` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36` |
| `win_edge_120` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0` |
| `win_firefox_120` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0` |

### デスクトップ（macOS）

| label | User-Agent |
|-------|------------|
| `mac_chrome_120` | `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36` |
| `mac_safari_17` | `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15` |
| `mac_firefox_120` | `Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0` |

### ボット / クローラー

| label | User-Agent |
|-------|------------|
| `googlebot_mobile` | `Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)` |
| `googlebot_desktop` | `Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)` |
| `bingbot` | `Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)` |

## 設定例

### 例1: iOS Safari と Android Chrome の2バリアントでWarmup

```javascript
const mainDocumentUserAgentList = [
  { label: 'ios_safari_17', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' },
  { label: 'android_chrome_pixel', ua: 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36' },
];

const assetUserAgentList = [
  { label: 'ios_safari_17', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' },
  { label: 'android_chrome_pixel', ua: 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36' },
];
```

### 例2: モバイルとデスクトップ両方でWarmup

```javascript
const mainDocumentUserAgentList = [
  { label: 'ios_safari_17', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' },
  { label: 'win_chrome_120', ua: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' },
];

const assetUserAgentList = [
  { label: 'ios_safari_17', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' },
];
```

### 例3: Googlebotも含めてSEO対策

```javascript
const mainDocumentUserAgentList = [
  { label: 'ios_safari_17', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' },
  { label: 'googlebot_mobile', ua: 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' },
];

const assetUserAgentList = [
  { label: 'ios_safari_17', ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' },
];
```

## URLタイプ別の動作

| urltype | 使用されるリスト | 説明 |
|---------|----------------|------|
| `main_document` | `mainDocumentUserAgentList` | HTMLページ本体 |
| `asset` | `assetUserAgentList` | CSS/JS/画像/フォント等 |
| `exception` | なし（スキップ） | Warmup対象外 |

## 注意事項

- 1つのURLに対して、リスト内の全User-Agentでリクエストが展開されます
- User-Agentを増やすと、リクエスト数が倍増します（URL数 × User-Agent数 × Request Engine数）
- 本番環境では、ターゲットユーザーに合わせた最小限のUser-Agentを選択することを推奨します

## 関連ドキュメント

- [N8N_WORKFLOW_README.md](N8N_WORKFLOW_README.md) - ワークフロー全体設定
- [NODE180_REQUESTENGINE_README.md](NODE180_REQUESTENGINE_README.md) - Request Engine設定（リージョン・言語）
