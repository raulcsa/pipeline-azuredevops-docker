from flask import Flask, jsonify
import os

app = Flask(__name__)


@app.route('/')
def home():
    return jsonify({
        'mensaje': 'Hola desde el contenedor Docker!',
        'version': '1.0.0',
        'entorno': os.getenv('ENTORNO', 'local')
    })


@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


@app.route('/suma/<int:a>/<int:b>')
def suma(a, b):
    return jsonify({'resultado': a + b})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
