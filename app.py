from flask import Flask, render_template, request
import config
from motoscraper import MotoScraper
from dataserializer import *


app = Flask(__name__)
app.config.from_object('config.BaseConfig')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/stats', methods=['POST'])
def stats():
    request.form['url']

    return render_template('stats.html', url=request.form['url'])


@app.route('/data', methods=['POST'])
def dataRequest():
    url = request.form['url']
    scraper = MotoScraper(url)
    data = prepare_full_data(scraper.data)

    return data



if __name__ == "__main__":
    app.run(threaded=True)
