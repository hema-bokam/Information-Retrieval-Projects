from flask import Flask, request, jsonify
import json
from linkedlist import LinkedList, Node  

from utils import (  
    preprocess_document,
    create_docId_tokens_map,
    get_total_documents,
    calculate_term_frequencies,
    calculate_total_terms_in_docs, 
    build_inverted_index,
    add_skip_pointers,
    add_tf_idf_scores,
    get_postings_lists,
    daat_AND,
    get_postings_lists_skip_pointers,
    daat_AND_skip,
    daat_AND_Tf_Idf,
    daat_and_skip_tfidf
)
import time

app = Flask(__name__)

inverted_index = None
docId_tokens_map = {}
total_docs = 0
term_frequencies = {}
total_terms_in_docs = {}


def initialize_index():
    global inverted_index, docId_tokens_map, total_docs, term_frequencies, total_terms_in_docs
    
    corpus_list = {}
    with open('input_corpus.txt', 'r', encoding='utf-8') as f:
        for line in f:
            doc_id, document = line.strip().split(maxsplit=1)
            # doc_id, document = line.strip().split("\t")
            corpus_list[int(doc_id)] = document
      
    docId_tokens_map = create_docId_tokens_map(corpus_list)
    total_docs = get_total_documents(docId_tokens_map)
    term_frequencies = calculate_term_frequencies(docId_tokens_map)
    total_terms_in_docs = calculate_total_terms_in_docs(docId_tokens_map)
    # build inverted index to the corpus
    inverted_index = build_inverted_index(docId_tokens_map)
    # add skip pointers to inverted index
    add_skip_pointers(inverted_index)
    # calculate tf-idf scores for each term in each document
    add_tf_idf_scores(inverted_index, term_frequencies, total_terms_in_docs, total_docs)
    

# server startup code -- preprocessing, building inverted index, adding skip pointers, and calculating tf-idf scores
initialize_index()

@app.route('/execute_query', methods=['POST'])
def execute_query():
    # queries = request.json["queries"]
    data = request.get_json()
    queries = data.get("queries", [])
    json_response = {}
    # Dictionary to store results for each query
    response = {
        "daatAnd": {},
        "daatAndSkip": {},
        "daatAndSkipTfIdf": {},
        "daatAndTfIdf": {},
        "postingsList": {},
        "postingsListSkip": {}
    }
    
    st = time.time()
    # sort the queries
    queries.sort()
    pos_list = get_postings_lists(queries, inverted_index)
    response["postingsList"] = get_postings_lists(queries, inverted_index)
    response["postingsListSkip"] = get_postings_lists_skip_pointers(queries, inverted_index)
    
    for query in queries:
        # Preprocess query
        query_terms = preprocess_document(query)
        
        # DAAT AND without skip pointers
        result_daat_and, comparisons_daat_and = daat_AND(query_terms, inverted_index)
        response["daatAnd"][query.strip()] = {
            "num_comparisons": comparisons_daat_and,
            "num_docs": len(result_daat_and.to_list() if result_daat_and else []),
            "results": result_daat_and.to_list() if result_daat_and else []
        }
        
        
        # DAAT AND with skip pointers
        result_daat_and_skip, comparisons_daat_and_skip = daat_AND_skip(query_terms, inverted_index)
        response["daatAndSkip"][query.strip()] = {
            "num_comparisons": comparisons_daat_and_skip,
            "num_docs": len(result_daat_and_skip.to_list() if result_daat_and_skip else []),
            "results": result_daat_and_skip.to_list() if result_daat_and_skip else []
        }
        
        # DAAT AND without skip, sorted by TF-IDF
        result_daat_and_tfidf = daat_AND_Tf_Idf(query_terms, inverted_index)
        response["daatAndTfIdf"][query.strip()] = result_daat_and_tfidf
        
        # DAAT AND with skip pointers, sorted by TF-IDF
        result_daat_and_skip_tfidf = daat_and_skip_tfidf(query_terms, inverted_index)
        response["daatAndSkipTfIdf"][query.strip()] = result_daat_and_skip_tfidf
        
    
    json_response["Response"] = response
    json_response["time_taken"] = time.time() - st
    
    # Save the response in sample_output.json
    with open("output.json", "w") as outfile:
        json.dump(json_response, outfile, indent=4)
    return jsonify( json_response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999)
