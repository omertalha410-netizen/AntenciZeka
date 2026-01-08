from flask import Flask, render_template, request, jsonify, session
import os
import requests

app = Flask(__name__)
app.secret_key = "antenci_gizli_key_123" # Hafıza (session) için bu şart hocam

# --- AYARLAR ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def index():
    # Sayfa ilk açıldığında hafızayı temizlemezsen eski konuşmalar kalabilir.
    # Eğer her yenilemede sıfırlansın istersen burayı kullanabilirsin.
    return render_template('index.html')

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    
    if not GROQ_API_KEY:
        return jsonify({"cevap": "Hocam Vercel'den GROQ_API_KEY eklenmemiş, dükkanın anahtarı eksik!"})

    # Hafızayı al (yoksa boş liste)
    history = session.get('history', [])

    # --- AKILLI SİSTEM TALİMATI ---
    system_instructions = (
        "Sen 'Antenci Zeka v2.5 Alfa'sın. Medrese Ekibi tarafından geliştirildim. "
        "DİL KURALI: Kesinlikle sadece TÜRKÇE konuş. Başka dillerden kelime veya yabancı alfabe karakterleri asla kullanma. "
        "HİTAP KURALI: Kullanıcıya 'Hocam' diye hitap et ama bunu her cümlede veya sürekli yapma. Sadece doğal bir selamlaşmada veya cümlenin başında/sonunda uygunsa kullan. Aşırıya kaçma. "
        "KİMLİK: Kim olduğun sorulmadığı sürece 'Medrese Ekibi tarafından eğitildim' deme. Kendini sürekli tanıtma. "
        "İÇERİK: Eğer soru bir okul dersi ise MEB/EBA müfredatına sadık kal. Günlük sohbet ise samimi, zeki ve kısa cevaplar ver."
    )

    # Mesaj geçmişini hazırla
    messages = [{"role": "system", "content": system_instructions}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": user_msg})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.6 # Hem zeki hem de biraz doğal olması için 0.6 idealdir.
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        cevap = res_json['choices'][0]['message']['content']
        
        # Hafızayı güncelle (Son 10 mesajı tutalım)
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": cevap})
        session['history'] = history[-10:]
        
        return jsonify({"cevap": cevap})
    except Exception as e:
        return jsonify({"cevap": f"Hocam bağlantıda bir sıkıntı çıktı: {str(e)}"})

@app.route('/login')
def login():
    session['user'] = {'name': 'Hocam'}
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')

if __name__ == "__main__":
    app.run()

