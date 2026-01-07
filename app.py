from flask import Flask, render_template, request, jsonify
import requests
import time

app = Flask(__name__)

# Daha stabil ve zeki olan 8B modeline geçiyoruz hocam
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    
    payload = {
        "inputs": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }

    # Hocam burada 3 kere deneme yapacak şekilde ayarladım
    for i in range(3):
        try:
            response = requests.post(API_URL, json=payload)
            res_json = response.json()
            
            # Eğer model yükleniyorsa (loading) hata verir, bekleyip tekrar deneriz
            if isinstance(res_json, dict) and "estimated_time" in res_json:
                time.sleep(5) # 5 saniye bekle ve döngüye devam et
                continue
                
            if isinstance(res_json, list) and len(res_json) > 0:
                cevap = res_json[0].get('generated_text', 'Hocam cevap boş geldi.')
                return jsonify({"cevap": cevap})
            
            # Eğer meşgul uyarısı gelirse biraz bekleyip tekrar dene
            time.sleep(2)
            
        except Exception as e:
            continue

    return jsonify({"cevap": "Hocam valla bu Hugging Face de biraz nazlı çıktı, bir 10 saniye sonra sayfayı yenileyip tekrar dene, model uyanacaktır."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
