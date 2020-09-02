#!/usr/bin/env python
# -*- coding: utf-8, euc-kr -*-

import numpy as np
import re
from gensim.models import Word2Vec
from scipy.spatial import distance
from gluonnlp.data import SentencepieceTokenizer
from kobert.utils import get_tokenizer
from tqdm import tqdm
from konlpy.tag import Mecab

class Modeling(object):
    def __init__(self):
        self.tok_path = get_tokenizer()
        self.sp = SentencepieceTokenizer(self.tok_path)
        self.v_dimension = 300
        self.v_window = 8
        self.hangul = re.compile("[^ㄱ-ㅎㅏ-ㅣ가-힣]+")
        self.mecab = Mecab()

    
    def kobert_tokenize_without_normal(self, kobert_news):
        # Remove letters which are not Hangul
        kobert_news_words = self.hangul.sub(' ', kobert_news)
        # Tokenization with KoBERT tokenizer
        kobert_token = self.sp(kobert_news_words)
        return kobert_token
    
    def mecab_tokenize_without_normal(self, mecab_news):
        # Remove letters which are not Hangul
        mecab_news_words = self.hangul.sub(' ', mecab_news)
         # Tokenization with Mecab tokenizer
        raw_token = self.mecab.morphs(mecab_news_words)
        stop_words = ['으로', '로도', '지만', '에서', '려는', '하다']
        for word in raw_token:
            if len(word) == 1:
                stop_words.append(word)
        mecab_token = [word for word in raw_token if word not in stop_words]
        return mecab_token

    def vectorize_without_normal(self, token):
        #Vectorization with word2vec
        #수정필요 sentence = [token]
        model = Word2Vec(sentences = token, size = self.v_dimension, window = self.v_window, min_count = 5, workers = 4, sg = 0)
        init_v = np.array([0.0]*self.v_dimension)
        for word in token:
            word_vectors = model.wv
            if word in word_vectors.vocab:
                v = model.wv[word]
                init_v = init_v + v
        return init_v
        


# Sample
if __name__ == "__main__":
    news= "(전국종합=연합뉴스) 3일 제9호 태풍 '마이삭'이 몰고 온 강력한 비바람으로 남부지역에 피해가 속출했다."
    Modeler = Modeling()
    kobert_token = Modeler.kobert_tokenize_without_normal(news)
    mecab_token = Modeler.mecab_tokenize_without_normal(news)
    model = Modeler.vectorize_without_normal(kobert_token)
    # Saving Model
    model.save('word2vec.model')



        


    
    
