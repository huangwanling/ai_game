import streamlit as st
import requests

# 網頁設定
st.set_page_config(page_title="阿吉的海龜湯", layout="wide")
st.title("🐢 阿吉的海龜湯猜謎實驗室")

# 核心參數
MODEL_NAME = "gemini-3.1-flash-lite"

# =====================================================================
# 1. 強化版提示詞：強制隱藏謎底，並設定遊戲目標
# =====================================================================
SYSTEM_PROMPT = """
你是一個嚴格的海龜湯主持人阿吉。
【遊戲目標】：請從「生活物品」、「職業」、「特定水果」、「日常事件」中選擇一個作為謎底。
【你的規則】：
1. 必須在內心秘密決定謎底，**絕對不要在對話中寫出謎底**。
2. 出題時，請明確告知玩家：謎底屬於哪一個大分類（例如：這是一件『物品』）。
3. 玩家提問時，只能回答：「是」、「不是」、「與此無關」、「不完全是」。
4. 唯有玩家猜中謎底，才可公布真相。
"""

def call_gemini_api(history, api_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    contents = [{"role": h['role'], "parts": [{"text": h['parts'][0]['text']}]} for h in history]
    data = {"contents": contents}
    
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        raise Exception(f"API錯誤 ({resp.status_code}): {resp.text}")

# =====================================================================
# 2. 初始化：確保第一步就是出題
# =====================================================================
if "history" not in st.session_state:
    init_cmd = "請選擇一個分類（物品、職業、水果、事件），秘密設定謎底，並出一道懸疑的謎題。在開頭請明確告訴玩家謎底屬於哪個分類。"
    st.session_state.history = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + init_cmd}]}]
    st.session_state.key_idx = 0
    
    try:
        keys = [st.secrets.get(f"GEMINI_API_KEY_{i}") for i in range(1, 6) if st.secrets.get(f"GEMINI_API_KEY_{i}")]
        resp = call_gemini_api(st.session_state.history, keys[0])
        st.session_state.history.append({"role": "model", "parts": [{"text": resp}]})
    except Exception as e:
        st.error(f"初始化出題失敗: {e}")

# =====================================================================
# 3. 渲染介面
# =====================================================================
for msg in st.session_state.history[1:]:
    role = "assistant" if msg["role"] == "model" else "user"
    st.chat_message(role, avatar="🐢" if role=="assistant" else None).write(msg["parts"][0]['text'])

# 互動邏輯
if user_input := st.chat_input("向阿吉提問..."):
    st.session_state.history.append({"role": "user", "parts": [{"text": user_input}]})
    with st.spinner("阿吉正在腦海中確認..."):
        try:
            keys = [st.secrets.get(f"GEMINI_API_KEY_{i}") for i in range(1, 6) if st.secrets.get(f"GEMINI_API_KEY_{i}")]
            resp = call_gemini_api(st.session_state.history, keys[st.session_state.key_idx % len(keys)])
            st.session_state.history.append({"role": "model", "parts": [{"text": resp}]})
            st.rerun()
        except Exception as e:
            if "429" in str(e):
                st.session_state.key_idx += 1
                st.warning("🐢 阿吉：這把鑰匙太累了，已切換下一把！")
                st.rerun()
            else:
                st.error(f"嚴重錯誤: {e}")

if st.sidebar.button("🔄 重置並換湯"):
    st.session_state.clear()
    st.rerun()