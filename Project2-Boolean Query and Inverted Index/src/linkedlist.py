import math

# Linkedlist node structure
class Node:
    def __init__(self, doc_id):
        self.doc_id = doc_id
        # maintains tf-idf score
        self.tf_idf = 0
        self.next = None
        # holds a skip pointer
        self.skip = None
        
        
# Linkedlist structure
class LinkedList:
    def __init__(self):
        self.head = None
        # stores the length of the linkedlist
        self.length = 0

# add a node to the linkedlist
    def add(self, doc_id_or_node):
        if isinstance(doc_id_or_node, Node):
            new_node = doc_id_or_node
        else:
            new_node = Node(doc_id_or_node)

        if self.head is None or self.head.doc_id > new_node.doc_id:
            new_node.next = self.head
            self.head = new_node
        else:
            current = self.head
            while current.next and current.next.doc_id < new_node.doc_id:
                current = current.next

            if current.doc_id != new_node.doc_id:
                new_node.next = current.next
                current.next = new_node
        self.length += 1


    # add skip pointers to the LL
    def add_skip_pointers(self):
        if self.length <= 2:
            return
        # total_skips = int(math.sqrt(self.length))
        dist_between_skips = int(round(math.sqrt(self.length)))
        # print(f"distance between skips: {distance_between_skips}")
        current = self.head
        prev_skip = self.head
        c = 0
        while current:
            if c == dist_between_skips:
                if prev_skip:
                    prev_skip.skip = current
                prev_skip = current
                c = 0
            current = current.next
            c += 1


    # I created this for testing skip pointers for the nodes
    # def print_skips(self):
    #     current = self.head
    #     while current:
    #         print(f"Doc ID: {current.doc_id}")
    #         if current.skip:
    #             print(f"Skip Pointer: {current.skip.doc_id}")
    #         current = current.next


    def calculate_tf_idf(self, term_frequency, len_postings_list, total_terms_in_docs, total_documents):
        current = self.head
        while current:
            # cal TF
            total_terms_doc = total_terms_in_docs[current.doc_id]
            token_freq_doc = term_frequency[current.doc_id]
            tf = token_freq_doc / total_terms_doc
            # cal IDF
            idf = total_documents / len_postings_list
            # cal TF-IDF
            current.tf_idf = tf * idf
            # print(f"Doc ID: {current.doc_id}, TF: {tf}, IDF: {idf}, TF-IDF: {current.tf_idf}")
            current = current.next


    def to_list(self):
        result = []
        current = self.head
        while current:
            result.append(current.doc_id)
            current = current.next
        return result
    
    # I created this for testing tf_idf scores 
    # def print_tf_idf(self):
    #     current = self.head
    #     while current:
    #         print(f"doc id: {current.doc_id}, tf-idf: {current.tf_idf:.6f}")
    #         current = current.next
