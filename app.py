from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# Vercel HTTPS hatası almamak için (Çok Önemli):
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# --- GOOGLE OAUTH AYARLARI ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = google.authorize_access_token()
    user = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    session['user'] = user
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- GERİ BİLDİRİM (FEEDBACK) KISMI ---
@app.route('/bildir', methods=['POST'])
def bildir():
    data = request.get_json()
    konu = data.get("konu", "")
    mesaj = data.get("mesaj", "")
    
    # Vercel Loglarına yazar (Deploy edince Log kısmında görürsün)
    print(f"\n📢 [YENİ BİLDİRİM]\nKonu: {konu}\nKullanıcı Notu: {mesaj}\n----------------\n")
    
    return jsonify({"durum": "basarili", "mesaj": "Geri bildirim alındı hocam!"})

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    history = session.get('history', [])

    # --- ANTENCİ ZEKA v3.0: TEK VE NET KARAKTER AYARI ---
    system_instructions = (
        "Sen 'Antenci Zeka'sın. Medrese Ekibi tarafından geliştirilen, v2.5 Beta aşamasında bir yapay zekasın. "
        "GÖREV VE DAVRANIŞ KURALLARI:\n"
        "1. DİL KURALI (EN ÖNEMLİ): Varsayılan dilin her zaman TÜRKÇE'dir. Kullanıcı teknik terimler (bug, code, error) kullansa bile Türkçe açıkla. "
        "Sadece kullanıcı açıkça 'Speak English' veya 'Çevir' derse o dile geç.\n"
        "2. ÜSLUP: Asla bağırma, büyük harflerle agresif cevaplar verme. Samimi, içten, nazik ve yardımsever ol.\n"
        "3. İFADE: Emojileri (🚀, 💡, ✅) kullanarak enerjini yansıt ama abartma. Robotik konuşma, sanki bir arkadaş gibi konuş.\n"
        "4. GÖREV: Kullanıcı ne sorarsa en doğru şekilde cevapla."
    )

    messages = [{"role": "system", "content": system_instructions}]
    
    # Geçmiş mesajları ekle
    for msg in history:
        messages.append(msg)
    
    messages.append({"role": "user", "content": user_msg})

    try:
        response = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.5 
        }, timeout=10)
        
        if response.status_code == 200:
            cevap = response.json()['choices'][0]['message']['content']
            
            history.append({"role": "user", "content": user_msg})
            history.append({"role": "assistant", "content": cevap})
            session['history'] = history[-10:] # Son 10 mesajı hatırla
            
            return jsonify({"cevap": cevap})
        else:
            return jsonify({"cevap": "Hocam şu an sunucularımda yoğunluk var, tekrar dener misin? 🚀"})
            
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"cevap": "Hocam bağlantıda ufak bir kopukluk oldu, tekrar dene istersen."})

if __name__ == "__main__":
    app.run()
