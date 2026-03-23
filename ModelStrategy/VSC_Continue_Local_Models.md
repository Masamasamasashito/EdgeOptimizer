# Gemma3 を VSCode「Continue」拡張で使う

Windows 11 (RTX5090 等) 環境において、Gemma3:27b を VSCode 上で動作させる手順

- `ModelStrategy` ディレクトリに移動してから実行してください。
- `Modelfile` は同ディレクトリにあらかじめ配置されているものとします。

## 1. ベースモデル取得

```bash
ollama pull gemma3:27b
```

## 2. カスタムモデル (Modelfile) の登録

すでに `ModelStrategy\Modelfile` が存在する場合、そのディレクトリで以下のコマンドを実行してカスタムモデルを登録します。

```powershell
# カスタムモデル登録
ollama create gemma3:27b-cc-ctx16k-v1 -f .\Modelfile
```

- ccはclaude code向けに準備したモデルであること
- ctxはコンテキスト長のこと、16384は16kトークンを意味する。適宜調整する。

## 3. モデル起動確認

```bash
ollama run gemma3:27b-cc-ctx16k-v1
# 正常にプロンプトが出ればOK。確認後は /bye で終了
```

## 4. VSCode 「Continue」拡張の設定

`C:\Users\ユーザー名\.continue\config.yaml` を開き、以下の設定を追加・更新

```yaml
models:
  - name: "gemma3:27b-cc-ctx16k-v1 (Ollama)"
    provider: "ollama"
    model: "gemma3:27b-cc-ctx16k-v1"
    apiBase: "http://localhost:11434"
    completionOptions:
      temperature: 0.1
      contextLength: 16384
```

## 5. VSCodeで使う

1. セカンダリサイドバーで、Continueを選択
2. チャットで、モデルは`gemma3:27b-cc-ctx16k-v1 (Ollama)` を選択
3. プロンプトを入力して、モデルを呼び出す