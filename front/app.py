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
        model_name = request.form['model']
        finrpt = FinRpt(model_name=model_name, save_path='./temp')
        temp_file = f"temp/{stock_code}_{date}_{model_name}/{stock_code}_{date}_{model_name}.pdf"
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
        'cookie': 'session=MTczMjYzNTkwNnxEWDhFQVFMX2dBQUJFQUVRQUFEX2pmLUFBQVVHYzNSeWFXNW5EQW9BQ0hWelpYSnVZVzFsQm5OMGNtbHVad3dLQUFocWFXNXpiMjVuT0FaemRISnBibWNNQmdBRWNtOXNaUU5wYm5RRUFnQUNCbk4wY21sdVp3d0lBQVp6ZEdGMGRYTURhVzUwQkFJQUFnWnpkSEpwYm1jTUJ3QUZaM0p2ZFhBR2MzUnlhVzVuREFVQUEzWnBjQVp6ZEhKcGJtY01CQUFDYVdRRGFXNTBCQUlBSkE9PXyQQwQIsjzk8UoPyjNt6A1V4b1z-mzsD3I2Cbbn3jz2Ew==',
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

@app.route('/get_logs')
def get_logs():
    log_file_path = request.args.get('path')
    log_file_path = log_file_path + '_gpt-4o'
    log_file_path = os.path.join('./temp', log_file_path, 'finrpt.log')
    print(log_file_path)
    try:
        with open(log_file_path, 'r') as f:
            logs = f.readlines()
        return {'log': logs[-1]}  # 返回最新一条日志
    except FileNotFoundError:
        return {'error': 'Log file not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)