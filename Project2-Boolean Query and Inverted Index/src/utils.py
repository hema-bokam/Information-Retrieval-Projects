import re
import nltk
from linkedlist import LinkedList, Node 
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from collections import defaultdict
nltk.download('stopwords')

# preprocessing a document or query
def preprocess_document(document):
    #convert lowercase 
    text = document.lower()
    # keep alphanumeric characters
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # print(text);
    #removes extra space
    text = re.sub(r'\s+', ' ', text).strip()
    # print(text)
    # extract the tokens
    tokens = text.split()
    # print(tokens)
    stop_words = set(stopwords.words('english'))
    # remove stopwords
    tokens = [word for word in tokens if word not in stop_words]
    # stemming
    stemmer = PorterStemmer()
    terms = [stemmer.stem(token) for token in tokens]
    return terms

# map of document ID to list of tokens
def create_docId_tokens_map(corpus_list):
    docId_tokens_map = {}
    for doc_id, document in corpus_list.items():
        docId_tokens_map[doc_id] = []
        docId_tokens_map[doc_id].extend(preprocess_document(document))
    return docId_tokens_map


# returns total number of documents
def get_total_documents(docId_tokens_map):
    return len(docId_tokens_map)


# calculating term frequencies, useful for calculating tf-idf values
# creates a map where term and docid are keys and value is frequency of term appearing in the document
def calculate_term_frequencies(docId_tokens_map):
    term_frequencies = {}
    for doc_id, tokens in docId_tokens_map.items():
        for term in tokens:
            if term not in term_frequencies:
                term_frequencies[term] = {}
            if doc_id not in term_frequencies[term]:
                term_frequencies[term][doc_id] = 0
            term_frequencies[term][doc_id] += 1
    return term_frequencies



# calculating total terms in the document id
def calculate_total_terms_in_docs(docId_tokens_map):
    total_terms_in_docs = {}
    for doc_id, tokens in docId_tokens_map.items():
        # if doc_id not in total_terms_in_docs:
        #     total_terms_in_docs[doc_id] = 0
        total_terms_in_docs[doc_id] = len(tokens)
    # print(total_terms_in_docs)
    return total_terms_in_docs


# build inverted index // mapping of term to linked list of doc ids
def build_inverted_index(docId_tokens_map):
    inverted_index = defaultdict(LinkedList)
    for doc_id, tokens in docId_tokens_map.items():
        unique_tokens = set(tokens)
        for token in unique_tokens:
            inverted_index[token].add(doc_id)
    return inverted_index

# add skip pointers for each posting list
def add_skip_pointers(inverted_index):
    for term, posting_list in inverted_index.items():
        # print(f"Adding skip pointers for term : {term}")
        posting_list.add_skip_pointers()
   
        
# cal tf-idf scores for each term in each document       
def add_tf_idf_scores(inverted_index, term_frequencies, total_terms_in_docs, total_documents):
    for term, posting_list in inverted_index.items():
        # total number of documents that has the term
        len_postings_list = posting_list.length
        # print(f"Term: {term} and len: {len_postings_list}")
        if len_postings_list > 0:
            posting_list.calculate_tf_idf(term_frequencies[term], len_postings_list, total_terms_in_docs, total_documents)
            
            
# returns unique terms in the queries
def get_unique_query_terms(queries):
    unique_terms = set()
    for query in queries:
        query_terms = preprocess_document(query)
        unique_terms.update(query_terms)
        #return list of unique terms 
    return list(unique_terms)

# PART 2.2: Get postings lists 
# returns postings list for the query terms
def get_postings_lists(queries, inverted_index):   
    query_terms = get_unique_query_terms(queries)
    # sort the terms
    query_terms.sort()
    postings_lists = {}
    for term in query_terms:
        postings_lists[term] = []
        if term in inverted_index:
            # if term == "coronaviru":
            #     print(f"Term: {term} and len: {inverted_index[term].length}")
            postings_lists[term] = inverted_index[term].to_list()
    return postings_lists
            


# Helper function to merge two postings lists with AND operation
def merge_intersect_AND_without_skip_pointers(p1, p2, num_comparisons):
    res = LinkedList()
    if not p1 or not p2:
        return res

    t1 = p1.head
    t2 = p2.head

    # Traverse both linked lists
    while t1 and t2:
        num_comparisons[0] += 1
        if t1.doc_id == t2.doc_id:
            new_node = Node(t1.doc_id)
            max_tf_idf = max(t1.tf_idf, t2.tf_idf)
            new_node.tf_idf = max_tf_idf
            res.add(new_node)
            t1, t2 = t1.next, t2.next
        elif t1.doc_id < t2.doc_id:
            t1 = t1.next
        else:
            t2 = t2.next

    return res


# PART 2.3: Document-at-a-time AND query without skip pointers 
def daat_AND(query_terms, inverted_index):
    postings_lists = [inverted_index[term] for term in query_terms if term in inverted_index]
    if not postings_lists or len(postings_lists) < len(query_terms):
        return [], 0

    postings_lists.sort(key=lambda lst: lst.length)
    num_comparisons = [0]
    result = postings_lists[0]
    for postings in postings_lists[1:]:
        result = merge_intersect_AND_without_skip_pointers(result, postings, num_comparisons)
        if not result:
            break
    return result, num_comparisons[0]



# PART 2.4: Get postings lists with skip pointers
def get_postings_lists_skip_pointers(queries, inverted_index):
    query_terms = get_unique_query_terms(queries)
    # sort the terms
    query_terms.sort()
    postings_list_with_skip_pointers = {}
    for term in query_terms:
        postings_list_with_skip_pointers[term] = []
        if term in inverted_index:
          postings_list = inverted_index[term]
          result = []
          current = postings_list.head
          if not (current and current.skip):
              continue
          result.append(current.doc_id)
          while current:
              if current.skip:
                  result.append(current.skip.doc_id)
                  current = current.skip
              else:
                  break
          postings_list_with_skip_pointers[term] = result if result else []
    return postings_list_with_skip_pointers



# Helper function to merge two postings lists with AND operation using skip pointers
def merge_intersect_AND_with_skip_pointers(p1, p2, num_comparisons):
    res = LinkedList()
    if not p1 or not p2:
        return res

    t1 = p1.head
    t2 = p2.head
    while t1 and t2:
        num_comparisons[0] += 1
        if t1.doc_id == t2.doc_id:
            new_node = Node(t1.doc_id)
            max_tf_idf = max(t1.tf_idf, t2.tf_idf)
            new_node.tf_idf = max_tf_idf
            res.add(new_node)
            t1, t2 = t1.next, t2.next
        elif t1.doc_id < t2.doc_id:
            if t1.skip and t1.skip.doc_id <= t2.doc_id:
                t1 = t1.skip
            else:
                t1 = t1.next
        else:
            if t2.skip and t2.skip.doc_id <= t1.doc_id:
                t2 = t2.skip
            else:
                t2 = t2.next

    return res

# PART 2.5: Document-at-a-time AND query with skip pointers 
def daat_AND_skip(query_terms, inverted_index):
    postings_lists = [inverted_index[term] for term in query_terms if term in inverted_index]
    if not postings_lists or len(postings_lists) < len(query_terms):
        return [], 0

    # Sort postings lists by length for optimizing comparisons
    postings_lists.sort(key=lambda lst: lst.length)
    num_comparisons = [0]
    result = postings_lists[0]
    for postings in postings_lists[1:]:
        result = merge_intersect_AND_with_skip_pointers(result, postings, num_comparisons)
        if not result:
            break

    return result, num_comparisons[0]



# PART 3.1: Document-at-a-time AND query without skip pointers, sorted by tf-idf
def daat_AND_Tf_Idf(query_terms, inverted_index):
    # AND query without skip pointers, and sort results tf-idf vals
    result, comparisons = daat_AND(query_terms, inverted_index)
    if not result:
        return {
            "num_comparisons": comparisons,
            "num_docs": 0,
            "results": []
        }
    tf_idf_scores = []
    current = result.head
    while current:
        tf_idf_scores.append((current.doc_id, current.tf_idf))
        current = current.next

    # print(tf_idf_scores)
    sorted_results_by_tf_idf = sorted(tf_idf_scores, key=lambda x: x[1], reverse=True)
    final_res = [doc_id for doc_id, _ in sorted_results_by_tf_idf]
    return {
        "num_comparisons": comparisons,
        "num_docs": len(final_res),
        "results": final_res
    }

# PART 3.2: Document-at-a-time AND query with skip pointers, sorted by tf-idf
def daat_and_skip_tfidf(query_terms, inverted_index):
    # AND query with skip pointers, and sort results by TF-IDF scores
    result, num_comparisons = daat_AND_skip(query_terms, inverted_index)

    if not result:
        return {
            "num_comparisons": num_comparisons,
            "num_docs": 0,
            "results": []
        }
    tf_idf_scores = []
    current = result.head
    while current:
        tf_idf_scores.append((current.doc_id, current.tf_idf))
        current = current.next
    sorted_results_by_skip_tf_idf = sorted(tf_idf_scores, key=lambda x: x[1], reverse=True)
    final_res = [doc_id for doc_id, _ in sorted_results_by_skip_tf_idf]
    return {
        "num_comparisons": num_comparisons,
        "num_docs": len(final_res),
        "results": final_res
    }
