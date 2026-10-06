---
name: switchbot-dashboard
description: SwitchBot 温湿度計の最新値を読んで、Artifact「おうちの空気」ダッシュボードに書き込む。「ダッシュボードを更新して」「おうちの空気を更新」などと頼まれたとき、または定期実行で使う。
---

# 「おうちの空気」ダッシュボードを更新する

ダッシュボード: https://claude.ai/artifact/F28YFnPuCqpMHncUUCyXtc
（ページのソースは `dashboard/switchbot-dashboard.html`。変更したら同じ URL に publish し直す）

## 手順

1. 値を読む。

   ```bash
   python3 switchbot.py meter --json
   ```

   エラーが出たら switchbot-meter スキルと同じ対応をする（環境変数・ネットワーク許可を頼む）。値をでっち上げて書き込まない。

2. `ArtifactData` の `list` で `meters` コレクションを読み、各ドキュメントの `version` と `history` を確認する。

3. 温湿度計 1 台につき 1 ドキュメント（`doc_id` は `deviceId`）を、`ArtifactData` の `batch` でまとめて `set` する。既存ドキュメントには読んだ `version` を `if_version` に付ける。

   ```json
   {
     "name": "リビング温湿度計",
     "deviceType": "MeterPro",
     "temperature": 22.5,
     "humidity": 41,
     "CO2": null,
     "battery": 90,
     "readAt": "2026-10-06T19:00:00+09:00",
     "history": [{"t": "2026-10-06T19:00:00+09:00", "temperature": 22.5, "humidity": 41, "CO2": null}]
   }
   ```

   - `history` は既存の配列の末尾に今回の値を足し、新しい方から 48 件だけ残す（古い順に並べる）。
   - 値がない項目は `null` のままでよい。
   - JSON に出てこなくなった温湿度計のドキュメントは消さない（ユーザーに聞く）。

4. 結果は「3 部屋を更新しました。寝室が乾燥気味です」のように短く伝える。
