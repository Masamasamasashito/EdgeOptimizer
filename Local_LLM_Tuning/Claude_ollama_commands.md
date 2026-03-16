# ローカルモデル指定claudeコマンドの基本

- 【入門記事】ClaudeCodeの中級者になりたい人は集合
    - https://qiita.com/K5K/items/72cc4282819ace823524

- LLM（Large Language Model / 大規模言語モデル）本質は「入力された文章に対し、確率的に最も自然な続きの文字列を返す」こと
- LLM単体は文章生成しかできない。ファイルを読んだり、コマンドを実行したり、外部サービスを操作したりする能力はない。
- Function Calling（Tool Use）で、LLMに「使えるツール一覧」を渡しておくと、LLMが状況に応じて適切なツールを選び、呼び出すことができる。
- LLM + Function Callingの組み合わせで、文章生成だけでなく「行動」が可能。
- コンテキスト・・・AIに渡す情報,文脈のこと
    - 会話の流れ、指定したファイルの中身、使えるツールの一覧などURLの内容、MCPやツールの実行結果など。
- コンテキストウィンドウ・・・AIが一度に扱える情報量の上限
    - 超えるとエラーや古い情報参照できなくなる
    - ClaudeCodeはコンテキストウィンドウ上限に近づくと `/compact` コマンドで自動的にコンテキスト圧縮する

# LLM実行時にコンテキストが扱われるデバイス

1. 入力「コンテキスト」は RAM に読み込まれる
2. 計算開始直前、データが VRAM へ送られる
3. GPUが VRAM 上データで計算、回答を出す

「VRAMが足りない」と言われるのは、「超高速な作業台」にデータが乗り切ってない状態。

|項目|RAM (Main Memory)|VRAM (Video RAM)|
|:---:|:---:|:---:|
|主な利用者|CPU (PCの脳)|GPU (画像・計算の専門家)|
|役割|OSやアプリ全体の作業場|映像描写・AI計算の専用作業場|
得意なこと|複雑な事務処理・複数アプリの管理|膨大な単純計算（行列演算など）|
|データ転送速度|高速|圧倒的に高速 (帯域が非常に広い)|
|物理的な場所|マザーボードのスロットに刺さる|グラフィックボードの中に内蔵|
|役割イメージ|広い事務机|超高速な専用作業台|

# MCP（Model Context Protocol）

- ClaudeCodeと外部ツール・サービスを連携させる仕組み
- Slack、GitHub、データベース等をMCPサーバーとして設定、ClaudeCodeが直接操作できるようになる
- MCPを設定すると、ツール実行結果がコンテキストに追加され、コンテキストを消費する

# Skills

- ClaudeCodeにタスクの手順やルールを教えるための仕組み
- マークダウンファイルで「業務マニュアル」を作成し、`.claude/skills/` フォルダに置く
- 必要なときに自動で呼び出される
- Skillsは呼び出されたときのみコンテキストを使う(Progressive Disclosure)
- コンテキスト効率の高さから、ClaudeCodeはSkillsが中心的な役割を担っている

# メモリ(ClaudeCode)

# ollama起動

以下で起動、ブラウザで　http://127.0.0.1:11434/　でOllamaの画面が見れます。
```
ollama serve
```

# モデルダウンロード

```
ollama pull qwen3.5:27b
ollama list
```

# shellでインタラクティブに(単純)モデル起動

```
ollama run qwen3.5:27b

# 出る
/bye
```

## モデル削除

```
ollama rm {モデル名}
# EX)
ollama rm qwen3.5:27b
```

# ローカルollama利用のための環境変数をセット

- Claudeは、デフォルトでAnthropicサーバーとの通信を想定。
- 明示的にローカルOllamaインスタンスにリダイレクトするため環境変数をセット。
- APIキーはダミー

```
$env:ANTHROPIC_BASE_URL = "http://localhost:11434/"
$env:ANTHROPIC_API_KEY = "ollama"
```
# 不要なトラフィックを抑制

- データ使用量制限やプライバシー重視の環境での利用を想定した設定
- テレメトリや非必須API呼び出しを停止

```
$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = "1"
```

## claude起動

```
claude --model qwen3.5:27b

claude --model gemma3:12b

claude --model deepseek-r1:14b
claude --model deepseek-r1:32b

claude --model gpt-oss:32b
```

## claude出る

```
exit
```

## インストール済モデル一覧
```

```

## Ollama Runコマンド

```
ollama run 
```

## Ollama モデル削除コマンド
```
ollama rm {モデル名}
```

## 抜ける/出る
```
/bye
```