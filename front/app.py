from flask import Flask, render_template, request, send_file, jsonify
from flask import send_from_directory
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from finrpt.module.FinRpt import FinRpt
import requests
import json
import os

app = Flask(__name__)

generation_count = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    try:
        stock_code = request.form['stock_code']
        date = request.form['date']
        model_name = "gpt-4o"
        finrpt = FinRpt(model_name=model_name, save_path='./temp')
        temp_file = f"temp/{stock_code}_{date}_{model_name}.pdf"
        finrpt.run(date=date, stock_code=stock_code)
        return jsonify({'pdf_file': temp_file, 'count': generation_count})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)})

@app.route('/download_pdf/<filename>')
def download_pdf(filename):
    return send_file(filename, as_attachment=True)

@app.route('/get_count')
def get_count():
    url = 'https://api.gptacg.top/api/token/?p=0&size=10'
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cookie': 'session=MTczMDcwNzM5NnxEWDhFQVFMX2dBQUJFQUVRQUFCdl80QUFCQVp6ZEhKcGJtY01CQUFDYVdRRGFXNTBCQUlBSkFaemRISnBibWNNQ2dBSWRYTmxjbTVoYldVR2MzUnlhVzVuREFvQUNHcHBibk52Ym1jNEJuTjBjbWx1Wnd3R0FBUnliMnhsQTJsdWRBUUNBQUlHYzNSeWFXNW5EQWdBQm5OMFlYUjFjd05wYm5RRUFnQUN83KQ2X4Y1ssY7CQE7VGuJQE4O8d-t1VbTPTsZmnfNTdM=',
        'new-api-user': '18',
        'referer': 'https://api.gptacg.top/token',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    }
    response = requests.get(url, headers=headers)
    print(response.text)
    generation_count = json.loads(response.text)['data'][0]["remain_quota"] / 5e5
    return jsonify({'count': generation_count})

@app.route('/temp/<path:filename>')
def download_file(filename):
    return send_from_directory('./temp', filename)

if __name__ == '__main__':
    app.run(debug=True)