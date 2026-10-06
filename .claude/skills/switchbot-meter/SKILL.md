---
name: switchbot-meter
description: SwitchBot の温湿度計（温湿度計Pro など）から今の温度・湿度・CO2・電池残量を読む。「部屋の温度は？」「湿度どう？」「温湿度計を見て」などと聞かれたときに使う。
---

# SwitchBot 温湿度計を読む

リポジトリの `switchbot.py` を使う。

```bash
python3 switchbot.py meter --json            # すべての温湿度計
python3 switchbot.py meter "<名前の一部>" --json  # 1台だけ
python3 switchbot.py devices                 # 名前が分からないとき
```

- 結果は日本語で短く伝える（例：「リビングは 22.5℃、湿度 41% です」）。
- 湿度が 40% 未満なら乾燥気味、60% を超えたら多湿気味とひと言添える。CO2 があれば 1000ppm 超で換気をすすめる。
- 電池が 20% 以下なら交換をすすめる。
- 「環境変数を設定してください」と出たら、`SWITCHBOT_TOKEN` と `SWITCHBOT_SECRET` の設定をユーザーに頼む。値をチャットに貼ってもらわない。
- 「API に接続できません」と出たら、ネットワーク設定で `api.switch-bot.com` が許可されているか確認してもらう。
