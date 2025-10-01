# scripts/fetch_aqi.py
# 作用：抓取 MoENV 即時空氣品質資料，正規化欄位後輸出到 repo 根目錄的 aqi.json
# 注意：API Key 從環境變數 MOENV_API_KEY 讀取（由 GitHub Actions secrets 提供）

import json, os, sys, time
from datetime import datetime, timezone
import requests

DATASET = os.getenv("MOENV_DATASET", "aqx_p_432")
API_KEY = os.getenv("MOENV_API_KEY")
BASE = f"https://data.moenv.gov.tw/api/v2/{DATASET}"

if not API_KEY:
    print("❌ 環境變數 MOENV_API_KEY 未設定", file=sys.stderr)
    sys.exit(1)

params = {
    "offset": 0,
    "limit": 1000,   # 抓寬一點
    "api_key": API_KEY,
}

def normalize(rec: dict) -> dict:
    """把可能出現的鍵名統一成前端容易使用的 snake_case。
       例如 'pm2.5' -> 'pm2_5'，全部轉成字串（數值讓前端再轉）。"""
    out = {}
    for k, v in rec.items():
        nk = k.lower()
        nk = nk.replace(".", "_").replace("-", "_")
        out[nk] = "" if v is None else str(v)
    # 常見欄位補齊（避免前端取不到 key）
    for k in ["sitename","aqi","pm2_5","pm10","no2","o3","so2","co","publishtime","status","county"]:
        out.setdefault(k, "")
    return out

def main():
    try:
        r = requests.get(BASE, params=params, timeout=20)
        r.raise_for_status()
        js = r.json()
        records = js.get("records", [])
        norm = [normalize(x) for x in records]

        # 增加快取輸出時間（UTC & local）
        out = {
            "source": BASE,
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "count": len(norm),
            "records": norm
        }

        with open("aqi.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        print(f"✅ 產生 aqi.json（{len(norm)} 筆）")

    except requests.HTTPError as e:
        print(f"❌ HTTP 錯誤：{e} - {getattr(e.response,'text','')[:200]}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ 其他錯誤：{e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
