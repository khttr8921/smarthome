import base64
import hashlib
import hmac
import unittest

import switchbot

DEVICES = [
    {"deviceId": "AAA", "deviceName": "リビング温湿度計", "deviceType": "MeterPro"},
    {"deviceId": "BBB", "deviceName": "寝室", "deviceType": "MeterPro(CO2)"},
    {"deviceId": "CCC", "deviceName": "ロボット掃除機", "deviceType": "Robot Vacuum Cleaner S10"},
    {"deviceId": "DDD", "deviceName": "玄関の人感センサー", "deviceType": "Motion Sensor"},
]

STATUS = {
    "AAA": {"temperature": 22.5, "humidity": 41, "battery": 90},
    "BBB": {"temperature": 21.0, "humidity": 48, "battery": 75, "CO2": 820},
    "DDD": {"battery": 10, "moveDetected": False},
}


class FakeClient:
    def devices(self):
        return DEVICES

    def status(self, device_id):
        return STATUS[device_id]


class SwitchBotTest(unittest.TestCase):
    def test_sign(self):
        h = switchbot.make_headers("tok", "sec", t="1700000000000", nonce="n")
        expected = base64.b64encode(
            hmac.new(b"sec", b"tok1700000000000n", hashlib.sha256).digest()
        ).decode()
        self.assertEqual(h["sign"], expected)
        self.assertEqual(h["Authorization"], "tok")

    def test_read_all_meters(self):
        results = switchbot.read_meters(FakeClient())
        self.assertEqual([r["deviceId"] for r in results], ["AAA", "BBB"])
        self.assertEqual(
            switchbot.format_meter(results[0]),
            "リビング温湿度計（MeterPro）: 温度 22.5℃ 湿度 41% 電池 90%",
        )
        self.assertIn("CO2 820ppm", switchbot.format_meter(results[1]))

    def test_query(self):
        results = switchbot.read_meters(FakeClient(), "リビング")
        self.assertEqual(len(results), 1)
        with self.assertRaises(switchbot.SwitchBotError):
            switchbot.read_meters(FakeClient(), "台所")

    def test_batteries(self):
        results = switchbot.read_batteries(FakeClient())
        self.assertEqual([r["deviceId"] for r in results], ["DDD", "BBB", "AAA"])
        self.assertTrue(results[0]["low"])
        self.assertFalse(results[1]["low"])
        self.assertEqual(
            switchbot.format_battery(results[0]),
            "玄関の人感センサー（Motion Sensor）: 電池 10% ← 交換してください",
        )


if __name__ == "__main__":
    unittest.main()
