from flask import Flask, request, jsonify
from pysolr import Solr

VM_IP = "34.85.223.192"
CORE_NAME = "IR24P3"
solr = Solr(f'http://{VM_IP}:8983/solr/{CORE_NAME}/', timeout=15)
app = Flask(__name__)

# solr = Solr(f'http://{VM_IP}:8983/solr/{CORE_NAME}/', timeout=10)
@app.route('/get_documents', methods=['POST'])
def get_relevant_documents_api():
    try:
        data = request.json
        query_string = data.get("query")
        topics = data.get("topics", [])
        k = data.get("k", 5)
        if not query_string or not topics:
            return jsonify({"error": "Query and topics are required"}), 400
        
        relevant_documents = []
        seen_documents = set() 
        titles = set()
        topics = [topic.capitalize() for topic in topics]
        for topic in topics:
            query = {
                'q': f'title:({query_string}) OR summary:({query_string})',
                'fq': f'topic:{topic}',
                'q.op': 'AND', 
                'rows': k,
                'df': 'summary'  
            }
            results = solr.search(**query)
            for result in results:
                title = result.get("title") 
                if title not in titles:
                    titles.add(title)
                    relevant_documents.append({
                        "title": result.get("title"),
                        "summary": result.get("summary"),
                        "topic": result.get("topic"),
                    })

        return jsonify({"documents": relevant_documents})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999)
