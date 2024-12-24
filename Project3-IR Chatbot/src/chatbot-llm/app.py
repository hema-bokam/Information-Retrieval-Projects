from flask import Flask, request, make_response
from common import GENERIC_RESPONSES
from openai import OpenAI
from collections import defaultdict


message_history = [{"role": "system", "content": "you are a chatbot."}]
client = OpenAI()
app = Flask(__name__)


def get_chat_response_gpt(prompt):
    message_history.append({"role": "user", "content": prompt})
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=message_history
    )
    response = str(completion.choices[0].message.content)
    message_history.append({"role": "system", "content": response})
    return response


def is_query(message):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"""'{message}'
                    is this a strong query regarding one or more topics.
                    Answer with "YES" only.
                    if it is chitchat or some chatbot message, answer with "NO" only.  
                """
            }
        ]
    )
    res = completion.choices[0].message.content
    return res == 'YES'


def summarize_documents(docs, query, topics):
    topics_str = ''
    docs_all = ''
    docs_per_topic = defaultdict(lambda: '')
    for doc in docs:
        docs_per_topic[doc['topic'].lower()] += doc['summary'] + '\n'
        docs_all = docs_all + doc['summary'] + '\n'
    topics = docs_per_topic.keys()
    for topic in topics:
        topics_str += topic + ', '
    if len(topics) == 0:
        text = f'Use the given DOCUMENTS and give an overall summary. It shouldnt be topic-based, return only high-level summary.\n DOCUMENTS is given below:\n{docs_all}'
    else:
        text = f'Use the given DOCUMENTS below for giving a summary regarding QUERY: {query} by involving TOPICS: {topics_str}' \
        + f'. For each topic, if documents are NOT related to it, skip it and DO NOT print in the response. Else add a summary for each topic, then ' \
        + 'put a Overall Documents Summary section where you summarize it as a whole.\n' \
        + f'DOCUMENTS is given below:\n{docs_all}'
    # text = f'There are documents returned for following QUERY: "{query}". ' \
    #     + 'Return the summary for the below TEXT (you may adjust it) it inorder to align with the given QUERY. ' \
    #     + f'Also, IMPROVISE based on "{query}". \n' \
    #     + 'DO NOT put your own comments and / or chatbot related words. It should be purely based on documents or your own improvisation. ' \
    #     + f'Your answer should be related to each of these topics: "f{topics_str}". If no relevant info in the text regarding majority of the topics, ' \
    #     + 'return something similar to "I am not able to respond to this query, could you adjust your query and topics" (ALTER THIS to increase diversity) ' \
    #     + '(do not mention about any failure of not being able find information in the given documents / text). ' \
    #     + 'Answer in this format: "**Summary of documents**: {overall summary about query involving each topic. }\n **{TOPIC_X}** (do this for each topic): {summary specifically for this topic}". \n' \
    #     + f'TEXT:\n{docs_all}'
    return get_chat_response_gpt(text)


@app.route("/get_bot_response", methods=['GET'])
def get_bot_response():
    user_text = request.args['message']
    if is_query(user_text):
        return make_response({'message': '', 'isQuery': True})
    return make_response({'message': get_chat_response_gpt(user_text), 'isQuery': False})


@app.route("/get_summary", methods=['GET'])
def get_summary():
    return make_response({
        'summary': summarize_documents(
            request.json['documents'],
            request.json['query'],
            request.json['topics']
        )
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3001)

