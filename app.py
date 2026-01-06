from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Hocam burası Hugging Face'in ücretsiz Llama 3 adresi
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    
    # Hugging Face için çok basit bir kurulum
    payload = {
        "inputs": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{user_msg}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }

    try:
        response = requests.post(API_URL, json=payload)
        res_json = response.json()
        
        # Cevabı temizleyip gönderiyoruz
        if isinstance(res_json, list) and len(res_json) > 0:
            cevap = res_json[0].get('generated_text', 'Hocam cevap boş geldi.')
            return jsonify({"cevap": cevap})
        else:
            return jsonify({"cevap": "Hocam şu an sunucu meşgul, 10 saniye sonra tekrar dene."})
            
    except Exception as e:
        return jsonify({"cevap": f"Hocam bir hata çıktı: {str(e)}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
