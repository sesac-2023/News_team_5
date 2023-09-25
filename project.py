from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import pandas as pd
import numpy as np

def load_news_data():
    with open('naver_data.pkl', 'rb') as f:
        data1 = pickle.load(f)
    return data1

def load_comments_data():
    data2 = pd.read_csv('naver_comments_all.csv')
    return data2

def group_user_ids_by_url(data2):
    data3 = data2.groupby('url')['user_id'].unique()
    return data3

def vectorize_data(data):
    data_str = data.apply(lambda x: ' '.join(x))
    
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(data_str)
    
    return X, vectorizer

def perform_lsa(X, n_components=10):
    svd = TruncatedSVD(n_components=n_components)
    lsa_result = svd.fit_transform(X)
    
    return lsa_result

def calculate_cosine_similarity(lsa_result):
    cosine_sim = cosine_similarity(lsa_result)
    
    return cosine_sim

def create_index_mapping(data_str):
     indices = pd.Series(range(len(data_str.index)), index=data_str.index)
     return indices
    
def preprocess_user_data(data2):
     df2_str_user = data2.groupby('user_id')['url'].apply(lambda x: ' '.join(x.values))
     
     vectorizer_user = CountVectorizer()
     X_user = vectorizer_user.fit_transform(df2_str_user)

     svd_user= TruncatedSVD(n_components=10) 
     lsa_result_user= svd_user.fit_transform(X_user)

     indices_user= pd.Series(range(len(df2_str_user.index)), index=df2_str_user.index)

     dict1= {name: id for id, name in zip(data2.user_id, data2.user_name)}
     
     return lsa_result_user, indices_user, dict1
    
# 기사링크 기반 추천시스템
def recommend(url, cosine_sim):
   idx= indices[url]
   sim_scores=list(enumerate(cosine_sim[idx]))
   sim_scores_sorted= sorted(sim_scores,key=lambda x:x[1], reverse=True )
   url_indices=[i[0] for i in sim_scores_sorted]
   
   # 가장 유사한 10개의 URL 반환하기 (자신 제외)
   top_10_urls=data3_str.index[url_indices][1:11]
   
   return top_10_urls
  
#유저기반 추천시스템 
 def recommend_urls_for_users(user_id): 
      idx=indices[user_id]
      sim_scores_url=list(enumerate(cosine_similarity(lsa_result[idx].reshape(1,-1),lsa_result)))
      sim_scores_url_sorted_indices=np.argsort(-np.array([i[1] for i in sim_scores_url]).flatten())
      top_5_similar_urls_indices=sim_scores_url_sorted_indices[:5]
      
      top_5_similar_urls=data3_str.index[top_5_similar_urls_indices]

      return top_5_similar_urls


if __name__ == '__main__':
  
  # 데이터 불러오기
  news_data = load_news_data()
  comments_data = load_comments_data()

  # 데이터 그룹화 및 전처리
  
  user_ids_by_url_grouped = group_users_ids_by_url(comments_data)

  
  # Counter Vectorization 및 LSA 수행
  
  X_grouped, vectorizer_grouped_newsdata =
vectorize_data(user_ids_by_url_grouped)

  
lsa_results_grouped =
perform_lsa(X_grouped)


cosine_similarity_grouped =
calculate_cosine_similarity(lsa_results_grouped)


index_mapping =
create_index_mapping(user_ids_by_url_grouped)



# 유저 데이터 전처리 및 딕셔너리 생성
 
lsa_results_users,
index_mapping_users,
dict_users =
preprocess_commentdata(comments_datagroupby_userid)



# 예시 실행 코드
 
url_recommendations =
recommend('news.naver.com',cosine_similarity_grouped)


user_recommendations =
recommend_urls_for_users(dict_users['user123'])


print("URL Recommendations:", url_recommendations)


print("User Recommendations:", user_recommendations)

