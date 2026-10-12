import json
from typing import Any

import httpx
from openai import OpenAI


class TravelAgent:
    API_KEY = "sk-22e0e41d47484fa0b0207d64efd24b1c"
    BASE_URL = "https://api.deepseek.com"
    MODEL = "deepseek-chat"
    MAX_ROUNDS = 5
    TIMEOUT = 15.0

    CITY_COORDS = {
        "北京": {"lat": 39.9042, "lon": 116.4074, "country": "中国"},
        "南京": {"lat": 32.0603, "lon": 118.7969, "country": "中国"},
    }

    WMO_CODE = {
        0: "晴", 1: "晴间多云", 2: "多云", 3: "阴",
        45: "雾", 48: "雾凇", 51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
        56: "冻毛毛雨", 57: "强冻毛毛雨", 61: "小雨", 63: "中雨", 65: "大雨",
        66: "冻雨", 67: "强冻雨", 71: "小雪", 73: "中雪", 75: "大雪", 77: "雪粒",
        80: "阵雨", 81: "强阵雨", 82: "暴雨", 85: "阵雪", 86: "强阵雪",
        95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷暴伴冰雹",
    }

    SYSTEM_PROMPT = """你是一个专业的旅游建议助手，目前只支持北京和南京两个城市。

【工作流程】
1. 当用户提到想去北京或南京时，你必须先调用 get_city_weather 查询该城市未来几天的天气。
2. 若用户未说明天数，默认查询 3 天；最长不超过 7 天。
3. 若用户提到的城市不在支持范围内，礼貌告知目前只支持北京和南京。
4. 拿到天气数据后，再结合天气给出旅游建议。

【输出结构】
一、🌤 天气概况（必须基于工具返回的真实数据，禁止编造）
二、🧥 穿衣建议（区分白天/早晚，说明温度与体感）
三、🗺 行程与景点建议（晴天推户外，雨天推室内博物馆等）
四、💡 出行小贴士（防晒/雨具/温差/交通等）

【要求】
- 语气亲切自然，像朋友给建议。
- 不要输出工具调用过程，直接给结论。
- 若工具返回错误，如实告知用户，不要编造天气。
"""

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_city_weather",
                "description": "查询北京或南京未来几天的天气，返回每日天气现象、最高/最低温度和降水概率。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "enum": ["北京", "南京"],
                            "description": "城市名称，目前只支持 北京 和 南京",
                        },
                        "days": {
                            "type": "integer",
                            "description": "查询天数，1-7 天，默认 3 天",
                        },
                    },
                    "required": ["city"],
                },
            },
        }
    ]

    def __init__(self, api_key: str = API_KEY):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

    @staticmethod
    def _clothing_hint(tmax: float, tmin: float, code: int) -> str:
        avg = (tmax + tmin) / 2
        if avg >= 30:
            base = "炎热：短袖短裤/裙装，注意防晒补水"
        elif avg >= 25:
            base = "热：短袖T恤、薄裤/裙装"
        elif avg >= 20:
            base = "温暖：长袖T恤/薄衬衫，早晚加薄外套"
        elif avg >= 15:
            base = "凉爽：薄外套/针织衫 + 长裤"
        elif avg >= 10:
            base = "微冷：夹克/风衣/薄毛衣 + 长裤"
        elif avg >= 5:
            base = "冷：厚外套/大衣 + 毛衣"
        elif avg >= 0:
            base = "寒冷：羽绒服/棉服 + 保暖内衣"
        else:
            base = "严寒：厚羽绒服、帽子手套围巾"

        extras = []
        if code in {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}:
            extras.append("有雨，带伞或防水外套")
        if code in {71, 73, 75, 77, 85, 86}:
            extras.append("有雪，注意防滑保暖")
        if code in {45, 48}:
            extras.append("有雾，能见度低，注意交通安全")
        if tmax - tmin >= 10:
            extras.append(f"昼夜温差约 {round(tmax - tmin)}℃，注意增减衣物")
        if tmax >= 28:
            extras.append("紫外线较强，做好防晒")
        return base + ("；" + "；".join(extras) if extras else "")

    def _get_city_weather(self, city: str, days: int = 3) -> dict[str, Any]:
        city = (city or "").strip()
        if city not in self.CITY_COORDS:
            return {"error": f"暂不支持城市「{city}」，目前仅支持：北京、南京。"}

        try:
            days = max(1, min(int(days), 7))
        except (TypeError, ValueError):
            days = 3

        coords = self.CITY_COORDS[city]
        try:
            resp = httpx.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": coords["lat"],
                    "longitude": coords["lon"],
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                    "timezone": "Asia/Shanghai",
                    "forecast_days": days,
                },
                timeout=self.TIMEOUT,
            )
            resp.raise_for_status()
            daily = resp.json()["daily"]
        except Exception as exc:
            return {"error": f"天气接口请求失败：{exc}"}

        forecast = []
        for i, date in enumerate(daily["time"]):
            code = daily["weather_code"][i]
            tmax = daily["temperature_2m_max"][i]
            tmin = daily["temperature_2m_min"][i]
            forecast.append({
                "date": date,
                "weather": self.WMO_CODE.get(code, f"未知({code})"),
                "temp_max": round(tmax),
                "temp_min": round(tmin),
                "precipitation_probability": daily["precipitation_probability_max"][i],
                "clothing_hint": self._clothing_hint(tmax, tmin, code),
            })

        return {
            "city": city,
            "country": coords["country"],
            "query_days": days,
            "forecast": forecast,
        }

    def chat(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})

        for _ in range(self.MAX_ROUNDS):
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=self.messages,
                tools=self.TOOLS,
                tool_choice="auto",
                temperature=1.0,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                content = msg.content or "（没有生成回复）"
                self.messages.append({"role": "assistant", "content": content})
                return content

            self.messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                print(f"[tool] {name}({args})")

                if name == "get_city_weather":
                    result = self._get_city_weather(**args)
                else:
                    result = {"error": f"未知工具：{name}"}

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        return "抱歉，工具调用轮数超限，请重新提问。"


def main():
    agent = TravelAgent()
    print("🧳 旅游建议助手已启动（仅支持 北京 / 南京，输入 q 退出）")
    print("   试试：我想去北京玩几天\n")

    while True:
        try:
            text = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见～")
            break

        if text.lower() in {"q", "quit", "exit"}:
            print("再见～")
            break
        if not text:
            continue

        try:
            print(f"\n助手：{agent.chat(text)}\n")
        except Exception as exc:
            print(f"❌ 出错：{exc}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()