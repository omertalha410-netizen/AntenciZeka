from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

# --- AYARLAR ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    
    if not GROQ_API_KEY:
        return jsonify({"cevap": "Hocam Vercel ayarlarından GROQ_API_KEY eklemeyi unutmuşuz!"})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Sen zeki bir asistansın. Kullanıcıya her zaman 'Hocam' dersin."},
            {"role": "user", "content": user_msg}
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        res_json = response.json()
        
        if "choices" in res_json:
            cevap = res_json['choices'][0]['message']['content']
            return jsonify({"cevap": cevap})
        else:
            return jsonify({"cevap": f"Hocam bir terslik var: {res_json.get('error', {}).get('message', 'Bilinmeyen hata')}"})
            
    except Exception as e:
        return jsonify({"cevap": f"Hocam bağlantı koptu: {str(e)}"})

# Vercel için bu kısım opsiyonel ama kalsın
if __name__ == "__main__":
    app.run()
