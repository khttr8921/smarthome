#!/usr/bin/env python3
"""SwitchBot API v1.1 の小さな CLI。

いまは温湿度計（温湿度計Pro など）の値を読むことだけに対応しています。
標準ライブラリだけで動きます。

環境変数:
  SWITCHBOT_TOKEN   SwitchBot アプリで発行したトークン
  SWITCHBOT_SECRET  同じ画面のクライアントシークレット

使い方:
  python3 switchbot.py devices            # デバイス一覧
  python3 switchbot.py meter              # 温湿度計をすべて読む
  python3 switchbot.py meter リビング      # 名前（または ID）で絞り込む
  python3 switchbot.py meter --json       # JSON で出力
  python3 switchbot.py battery            # 電池で動く機器の残量
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API_BASE = "https://api.switch-bot.com/v1.1"

# deviceId ごとの表示名と屋外かどうか（SwitchBot アプリの名前より優先）
OVERRIDES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices.json")

# 温度・湿度を返すデバイスの種類（deviceType）
METER_TYPES = {
    "Meter",
    "MeterPlus",
    "MeterPro",
    "MeterPro(CO2)",
    "WoIOSensor",
    "Hub 2",
}


# 電池で動き、ステータスに battery を返すデバイスの種類
BATTERY_TYPES = METER_TYPES - {"Hub 2"} | {
    "Bot",
    "Curtain",
    "Curtain3",
    "Blind Tilt",
    "Roller Shade",
    "Motion Sensor",
    "Contact Sensor",
    "Water Detector",
    "Smart Lock",
    "Smart Lock Pro",
    "Keypad",
    "Keypad Touch",
}

LOW_BATTERY = 20


class SwitchBotError(Exception):
    pass


def make_headers(token, secret, t=None, nonce=None):
    """API v1.1 の署名付きヘッダーを作る。"""
    t = t or str(int(time.time() * 1000))
    nonce = nonce or str(uuid.uuid4())
    string_to_sign = f"{token}{t}{nonce}".encode("utf-8")
    sign = base64.b64encode(
        hmac.new(secret.encode("utf-8"), string_to_sign, hashlib.sha256).digest()
    ).decode("utf-8")
    return {
        "Authorization": token,
        "sign": sign,
        "t": t,
        "nonce": nonce,
        "Content-Type": "application/json; charset=utf8",
    }


class Client:
    def __init__(self, token, secret):
        self.token = token
        self.secret = secret

    @classmethod
    def from_env(cls):
        token = os.environ.get("SWITCHBOT_TOKEN")
        secret = os.environ.get("SWITCHBOT_SECRET")
        if not token or not secret:
            raise SwitchBotError(
                "環境変数 SWITCHBOT_TOKEN と SWITCHBOT_SECRET を設定してください。"
            )
        return cls(token, secret)

    def get(self, path):
        req = urllib.request.Request(
            API_BASE + path, headers=make_headers(self.token, self.secret)
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                data = json.load(res)
        except urllib.error.HTTPError as e:
            raise SwitchBotError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}")
        except urllib.error.URLError as e:
            raise SwitchBotError(f"API に接続できません: {e.reason}")
        if data.get("statusCode") != 100:
            raise SwitchBotError(
                f"API エラー {data.get('statusCode')}: {data.get('message')}"
            )
        return data["body"]

    def devices(self):
        return self.get("/devices").get("deviceList", [])

    def status(self, device_id):
        return self.get(f"/devices/{device_id}/status")


def load_overrides(path=OVERRIDES_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def apply_overrides(devices, overrides):
    """devices.json の表示名を deviceName に反映し、outdoor を付ける。"""
    result = []
    for d in devices:
        o = overrides.get(d.get("deviceId"), {})
        d = dict(d)
        if o.get("name"):
            d["deviceName"] = o["name"]
        d["outdoor"] = bool(o.get("outdoor"))
        result.append(d)
    return result


def find_meters(devices, query=None):
    meters = [d for d in devices if d.get("deviceType") in METER_TYPES]
    if query:
        meters = [
            d for d in meters
            if query in (d.get("deviceName") or "") or query == d.get("deviceId")
        ]
    return meters


def read_meters(client, query=None, overrides=None):
    devices = apply_overrides(client.devices(), overrides if overrides is not None else load_overrides())
    meters = find_meters(devices, query)
    if not meters:
        raise SwitchBotError(
            "温湿度計が見つかりません。"
            + ("名前を確認してください。" if query else "クラウドサービスが有効か確認してください。")
        )
    results = []
    for d in meters:
        s = client.status(d["deviceId"])
        results.append({
            "name": d.get("deviceName"),
            "deviceId": d["deviceId"],
            "deviceType": d.get("deviceType"),
            "temperature": s.get("temperature"),
            "humidity": s.get("humidity"),
            "battery": s.get("battery"),
            "CO2": s.get("CO2"),
            "outdoor": d["outdoor"],
        })
    return results


def read_batteries(client, overrides=None):
    """電池で動く機器の残量を、少ない順に返す。"""
    results = []
    devices = apply_overrides(client.devices(), overrides if overrides is not None else load_overrides())
    for d in devices:
        if d.get("deviceType") not in BATTERY_TYPES:
            continue
        battery = client.status(d["deviceId"]).get("battery")
        if battery is None:
            continue
        results.append({
            "name": d.get("deviceName"),
            "deviceId": d["deviceId"],
            "deviceType": d.get("deviceType"),
            "battery": battery,
            "low": battery <= LOW_BATTERY,
        })
    results.sort(key=lambda r: r["battery"])
    return results


def format_battery(r):
    line = f"{r['name']}（{r['deviceType']}）: 電池 {r['battery']}%"
    return line + " ← 交換してください" if r["low"] else line


def format_meter(r):
    parts = [f"{r['name']}（{r['deviceType']}）:"]
    if r["temperature"] is not None:
        parts.append(f"温度 {r['temperature']}℃")
    if r["humidity"] is not None:
        parts.append(f"湿度 {r['humidity']}%")
    if r["CO2"] is not None:
        parts.append(f"CO2 {r['CO2']}ppm")
    if r["battery"] is not None:
        parts.append(f"電池 {r['battery']}%")
    return " ".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description="SwitchBot API CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dev = sub.add_parser("devices", help="デバイス一覧を表示")
    p_dev.add_argument("--json", action="store_true")

    p_meter = sub.add_parser("meter", help="温湿度計の値を読む")
    p_meter.add_argument("query", nargs="?", help="デバイス名の一部、または deviceId")
    p_meter.add_argument("--json", action="store_true")

    p_bat = sub.add_parser("battery", help="電池で動く機器の残量を表示")
    p_bat.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    try:
        client = Client.from_env()
        if args.cmd == "devices":
            devices = apply_overrides(client.devices(), load_overrides())
            if args.json:
                print(json.dumps(devices, ensure_ascii=False, indent=2))
            else:
                for d in devices:
                    print(f"{d.get('deviceName')}\t{d.get('deviceType')}\t{d.get('deviceId')}")
        elif args.cmd == "meter":
            results = read_meters(client, args.query)
            if args.json:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                for r in results:
                    print(format_meter(r))
        elif args.cmd == "battery":
            results = read_batteries(client)
            if args.json:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                for r in results:
                    print(format_battery(r))
    except SwitchBotError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
