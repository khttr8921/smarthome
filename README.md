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

## ダッシュボード（Artifact）

温湿度計の値を部屋ごとに見られるページ「おうちの空気」を Artifact として公開しています（非公開・オーナーのみ閲覧可）。

- ページ: https://claude.ai/artifact/F28YFnPuCqpMHncUUCyXtc
- ソース: `dashboard/switchbot-dashboard.html`

ページ自体は SwitchBot API に直接つながりません（トークンをブラウザに置かないため）。Claude Code に「ダッシュボードを更新して」と頼むと、`.claude/skills/switchbot-dashboard/` のスキルが `switchbot.py meter --json` の結果をページのデータベースに書き込みます。定期的に更新したいときは、トークンとネットワーク許可を設定した環境で Routine（定期実行）からこの依頼を送ってください。

## テスト

```bash
python3 -m unittest -v
```
