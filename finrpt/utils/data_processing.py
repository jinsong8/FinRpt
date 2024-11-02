import gc
from datasketch import MinHash, MinHashLSH
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
import random
import json
import re
import pdb

# Duplication
def duplication_eliminate_hash (news):
    lsh = MinHashLSH(threshold=0.3, num_perm=128)
    for i, new in enumerate(news):
        text  = new['news_title'] + '\n' + new['news_content']
        minhash = MinHash(num_perm=128)
        for word in text.split():
            minhash.update(word.encode('utf-8'))
        lsh.insert(str(i), minhash)

    unique_documents = set()

    for i, new in enumerate(news):
        text = new["news_time"] + '\n' + new["news_title"] + "\n" + new["news_content"]
        query_minhash = MinHash(num_perm=128)
        for word in text.split():
            query_minhash.update(word.encode('utf-8'))
        results = lsh.query(query_minhash)
        try:
            unique_documents.add(results[0])
        except Exception as e:
            print(f'error: {e}')
    total_unique_documents = len(unique_documents)
    total_documents = len(news)
    duplication_ratio = (total_documents - total_unique_documents) / total_documents
    unique_documents = [news[int(i)] for i in unique_documents]
    unique_documents = sorted(unique_documents, key=lambda x: x['news_time'], reverse=True)
    return unique_documents, duplication_ratio

# Duplication
def duplication_eliminate_bert (news):
    documents = [new["news_time"] + '\n' + new["news_title"] + "\n" + new["news_content"] for new in news]
    model = SentenceTransformer('BAAI/bge-large-zh-v1.5')
    batch_size = 512
    embeddings = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_embeddings = model.encode(
            batch,
            normalize_embeddings=True
        )
        embeddings.extend(batch_embeddings)
    cosine_sim = cosine_similarity(embeddings, embeddings)
    
    threshold = 0.9

    to_remove = set()
    for i in range(len(documents)):
        for j in range(i + 1, len(documents)):
            if cosine_sim[i, j] > threshold:
                to_remove.add(j)

    filtered_news = [a for i, a in enumerate(news) if i not in to_remove]

    return filtered_news, len(to_remove) / len(news)

# Too Short news
def short_eliminate(news, min_len=50):
    filter_news = [new for new in news if len(new["news_content"]) > min_len]
    return filter_news, 1 - len(filter_news) / len(news)

def filter_news_by_date(news, max_news_per_day=3):
    date2news = {}
    for new in news:
        date = new["news_time"]
        if date not in date2news:
            date2news[date] = []
        date2news[date].append(new)
        
    filtered_news = []
    for date, date_news in date2news.items():
        if len(date_news) > max_news_per_day:
            filtered_news.extend(random.sample(date_news, k=max_news_per_day))
        else:
            filtered_news.extend(date_news)
            
    
    filtered_news = sorted(filtered_news, key=lambda x: x['news_time'], reverse=True)
    return filtered_news, 1 - len(filtered_news) / len(news)

def limit_by_amount(news, amount):
    if len(news) <= amount:
        return news, 1
    else:
        news = random.sample(news, k=amount)
        return news, 1 - len(news) / len(news)

def robust_load_json(text):
    try:
        response_json = json.loads(text[7:-3].strip())
        return response_json
    except Exception as e:
        try:
            response_json = json.loads(text)
            return response_json
        except Exception as e:
            pass
    
    try:
        json_pattern = r'\{(?:[^{}]|(?R))*\}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        raise ValueError("No valid JSON object found")
    
    except Exception as e:
        raise ValueError("No valid JSON object found")
    
