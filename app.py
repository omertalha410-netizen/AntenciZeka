import google.generativeai as genai
import os
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "antenci_final_v2026"

# API Ayarı
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

user_quotas = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    email = request.remote_addr # Şimdilik en basit yöntemle gidelim
    
    # 2026'da kotaları en stabil olan çekirdek model:
    try:
        # HOCAM DİKKAT: En 'eski' ama en 'açık' model budur.
        model = genai.GenerativeModel('gemini-1.0-pro') 
        response = model.generate_content(user_msg)
        return jsonify({"cevap": response.text})
    except Exception as e:
        # Eğer bu da olmazsa, tek bir alternatifimiz kalıyor:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-8b') # En küçük model
            response = model.generate_content(user_msg)
            return jsonify({"cevap": response.text})
        except:
            return jsonify({"cevap": f"Hocam Google bu anahtarı/IP'yi tamamen kilitledi. Hata: {str(e)}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
