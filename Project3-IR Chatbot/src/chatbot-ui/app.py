from flask import Flask, render_template, request
import requests
import markdown
import common
from collections import defaultdict
import time

app = Flask(__name__)
stats = {
    'dist': defaultdict(lambda: 0),
    'length': [],
    'type': [0, 0],
    'freq_by_multi_topics': defaultdict(lambda: 0),
    'response_times': []
}


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/visualization')
def visualization():
    return render_template('visualization.html', **stats)


@app.route("/execute_raw_text", methods=['GET'])
def execute_raw_text():
    try:
        start_time = time.time()
        message = request.args.get('message')
        topics = request.args.getlist('topics[]')
        if 'all' in topics or len(topics) == 0:
            topics = common.get_default_topics()
        res = requests.get(' http://127.0.0.1:3001/get_bot_response', params={'message': message}).json()
        stats['length'].append(len(message))
        if res['isQuery']:
            for topic in topics:
                stats['dist'][topic] += 1
            if len(topics) > 1:
                topics_key = '('
                for topic in topics:
                    topics_key += topic
                    if topic != topics[-1]:
                        topics_key += ', '
                topics_key += ')'
                if len(topics) == 10:
                    topics_key = '(all)'
                print(topics_key)
                stats['freq_by_multi_topics'][topics_key] += 1
            stats['type'][1] += 1
            res = requests.post(
                ' http://34.85.223.192:9999/get_documents',
                json={'query': message, 'topics': topics, 'k': 3}
            ).json()
            res_summary = requests.get(
                ' http://127.0.0.1:3001/get_summary',
                json={'documents': res['documents'], 'query': message, 'topics': topics}
            ).json()
            end_time = time.time()
            stats['response_times'].append(end_time - start_time)
            return markdown.markdown(res_summary['summary'])
        stats['type'][0] += 1
        end_time = time.time()
        stats['response_times'].append(end_time - start_time)
        return markdown.markdown(res['message'])
    except:
        return markdown.markdown('There are some issues in the servers right now. Please try again later.')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)
