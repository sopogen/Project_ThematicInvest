#!/usr/bin/env python
# -*- coding: utf-8, euc-kr -*-

import numpy as np
import re
from gensim.models import Word2Vec
from scipy.spatial import distance
from gluonnlp.data import SentencepieceTokenizer
from kobert.utils import get_tokenizer
from tqdm import tqdm

class Modeling(object):
    def __init__(self):
        self.tok_path = get_tokenizer()
        self.sp = SentencepieceTokenizer(self.tok_path)
        self.v_dimension = 300
        self.v_window = 8

    
    def tokenize_without_normal(self, news):
        # Remove letters which are not Hangul
        hangul = re.compile("[^ㄱ-ㅎㅏ-ㅣ가-힣]+")
        news_words = hangul.sub(' ', news)
        # Tokenization with KoBERT tokenizer
        token = self.sp(news_words)
        return token

    def vectorize_without_normal(self, token):
        #Vectorization with word2vec
        model = Word2Vec(sentences = token, size = self.v_dimension, \
            window = self.v_window, min_count = 5, workers = 4, sg = 0)

        init_v = np.array([0.0]*self.v_dimension)
        for word in token:
            word_vectors = model.wv
            if word in word_vectors.vocab:
                v = model.wv[word]
                init_v = init_v + v
        return init_v  
        


if __name__ == "__main__":
    news= "유럽연합(EU) 집행위원회는 2일(현지시간) 현대차 그룹이 유럽의 전기차 충전 인프라 업체인"
    Modeler = Modeling()
    token = Modeler.tokenize_without_normal(news)
    result = Modeler.vectorize_without_normal(token)
    print(result)
