from flask import Flask, render_template, request, jsonify
import os
import requests

app = Flask(__name__)

# --- AYARLAR ---
# Vercel Settings -> Environment Variables kısmına GROQ_API_KEY eklediğinden emin ol hocam.
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
        return jsonify({"cevap": "Hocam Vercel ayarlarından GROQ_API_KEY eklenmemiş, dükkanın anahtarı eksik!"})

    # --- MEDRESE v2.5 ALFA SİSTEM TALİMATI ---
    system_instructions = (
        "Sen 'Medrese' ve Hocan tarafından geliştirilen, 'v2.5 alfa' sürümündeki eğitim asistanısın. "
        "Birincil görevin öğrencilere ödevlerinde yardımcı olmak, konu anlatımı yapmak ve eğitici sohbetler etmektir. "
        "Ödevlerle ilgili sorularda kesinlikle Türkiye Cumhuriyeti Milli Eğitim Bakanlığı (MEB) müfredatını, "
        "OGM Materyal içeriklerini ve EBA (Eğitim Bilişim Ağı) standartlarını temel alarak cevap vermelisin. "
        "Kullanıcıya her zaman 'Hocam' diye hitap etmelisin. "
        "Kim olduğun sorulursa Medrese v2.5 alfa olduğunu ve Hocan tarafından eğitildiğini söylemelisin."
    )

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.5 # Eğitim için daha tutarlı cevaplar vermesi için düşürdüm hocam.
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
            return jsonify({"cevap": f"Hocam bir hata var: {res_json.get('error', {}).get('message', 'Bilinmeyen hata')}"})
            
    except Exception as e:
        return jsonify({"cevap": f"Hocam bağlantıda bir sıkıntı çıktı: {str(e)}"})

if __name__ == "__main__":
    app.run()
