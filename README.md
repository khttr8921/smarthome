# smarthome

Claude Code から SwitchBot API（v1.1）でスマートホーム機器を扱うためのリポジトリです。
いまは温湿度計（温湿度計Pro など）の値を読むことに対応しています。標準ライブラリだけで動きます（Python 3.8 以上）。

## 準備

1. SwitchBot アプリで「プロフィール → 設定 → アプリバージョン」を10回タップし、「開発者向けオプション」からトークンとクライアントシークレットを取得します。
2. 温湿度計の設定で「クラウドサービス」をオンにします（オフだと API に出てきません）。
3. 環境変数を設定します。

   ```bash
   export SWITCHBOT_TOKEN=...
   export SWITCHBOT_SECRET=...
   ```

   Claude Code のクラウド環境で使うときは、環境の設定で上の2つを環境変数に入れ、Network access で `api.switch-bot.com` を許可してください。

## 使い方

```bash
python3 switchbot.py devices          # デバイス一覧
python3 switchbot.py meter            # 温湿度計をすべて読む
python3 switchbot.py meter リビング    # 名前で絞り込む
python3 switchbot.py meter --json     # JSON で出力
```

出力例:

```
リビング温湿度計（MeterPro）: 温度 22.5℃ 湿度 41% 電池 90%
```

Claude Code では `.claude/skills/switchbot-meter/` のスキルが入っているので、「部屋の湿度は？」と聞くだけで読みにいきます。

## テスト

```bash
python3 -m unittest -v
```
