from flask import Flask, render_template, request
from scraper import MotoScraper
from dataserializer import *


app = Flask(__name__)
app.config.from_object('config.BaseConfig')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stats', methods=['POST'])
def stats():
    url = request.form['url']
    return render_template('stats.html', url=url)


@app.route('/data', methods=['POST'])
def data_endpoint():
    url = request.form['url']
    scraper = MotoScraper()
    offers = scraper.get_offers(url)
    data = prepare_full_data(offers)
    return data


if __name__ == "__main__":
    app.run(threaded=True)
