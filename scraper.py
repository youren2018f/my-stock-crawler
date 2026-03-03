import requests
from bs4 import BeautifulSoup
import os

# 從 GitHub Secrets 安全讀取 Discord Webhook 網址
# 請確保你在 GitHub Settings > Secrets > Actions 中設定了 DISCORD_WEBHOOK
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def send_discord(msg):
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ 錯誤：找不到 DISCORD_WEBHOOK 環境變數")
        return
    
    payload = {"content": msg}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print("✅ Discord 通知發送成功！")
        else:
            print(f"❌ 通知失敗，狀態碼：{response.status_code}")
    except Exception as e:
        print(f"⚠️ 發送異常：{e}")

def main():
    url = "https://histock.tw/stock/public.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    print(f"📡 正在抓取資料：{url}")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 根據診斷結果，直接抓取網頁中第一個 table
        tables = soup.find_all('table')
        if not tables:
            print("❌ 網頁中找不到任何表格")
            return
            
        table = tables[0]
        rows = table.find_all('tr')[1:] # 跳過標題列
        
        # 讀取已通知過的歷史紀錄 (history.txt)
        notified_list = []
        if os.path.exists('history.txt'):
            with open('history.txt', 'r', encoding='utf-8') as f:
                notified_list = f.read().splitlines()

        found_new = False
        
        for row in rows:
            cols = row.find_all('td')
            # 確保欄位數量符合預期 (至少要到狀態欄索引 13)
            if len(cols) < 14:
                continue
            
            # 欄位對齊：[1]代號名稱, [8]獲利, [13]狀態
            raw_id_name = cols[1].get_text(strip=True).replace('\xa0', ' ')
            profit_str = cols[8].get_text(strip=True).replace(',', '')
            status = cols[13].get_text(strip=True)
            
            # 拆分代號與名稱
            parts = raw_id_name.split(' ')
            stock_id = parts[0]
            stock_name = parts[1] if len(parts) > 1 else "未知名稱"

            # 處理獲利數字
            try:
                profit = int(profit_str)
            except ValueError:
                profit = 0

            # 🚩 判斷條件：包含 "申購中" 且 獲利 > 5000
            if "申購中" in status and profit > 5000:
                if stock_id not in notified_list:
                    print(f"🎯 發現符合條件：{stock_id} {stock_name}, 獲利: {profit}")
                    
                    msg = (f"🚀 **【股票申購提醒】**\n"
                           f"🔹 股票：{stock_name} ({stock_id})\n"
                           f"💰 預估報酬：${profit:,} 元\n"
                           f"📝 狀態：{status}\n"
                           f"🔗 傳送門：{url}")
                    
                    send_discord(msg)
                    
                    # 紀錄到 history.txt 避免重複
                    with open('history.txt', 'a', encoding='utf-8') as f:
                        f.write(stock_id + '\n')
                    notified_list.append(stock_id)
                    found_new = True
                else:
                    print(f"⏭️  {stock_id} 已通知過，跳過。")

        if not found_new:
            print("✅ 掃描完成，目前無符合條件的新股票。")

    except Exception as e:
        print(f"❌ 執行出錯：{e}")

if __name__ == "__main__":
    main()
