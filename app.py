from flask import Flask, render_template, request, jsonify, session
import os
import requests

app = Flask(__name__)
app.secret_key = "antenci_gizli_key_123" # Session için gerekli hocam

# --- AYARLAR ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Şimdilik giriş yapılmış gibi simüle ediyoruz hocam
    session['user'] = {'name': 'Misafir Hocam'}
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('index.html')

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    
    if not GROQ_API_KEY:
        return jsonify({"cevap": "Hocam Vercel ayarlarından GROQ_API_KEY eklenmemiş!"})

    system_instructions = (
        "Sen 'Medrese' ve Hocan tarafından geliştirilen, 'v2.5 alfa' sürümündeki eğitim asistanısın. "
        "Kullanıcıya her zaman 'Hocam' diye hitap etmelisin. MEB müfredatına uygun cevaplar vermelisin."
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.5
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        cevap = res_json['choices'][0]['message']['content']
        return jsonify({"cevap": cevap})
    except Exception as e:
        return jsonify({"cevap": f"Hocam bir sıkıntı çıktı: {str(e)}"})

if __name__ == "__main__":
    app.run()
