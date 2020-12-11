# Project_ThematicInvest
> NLP를 이용하여 뉴스 데이터를 통한 테마주 찾기  
> For 2020-1 ybigta conference

## Background
- 최근 주식시장에 대한 접근성 향상으로 많은 가계들이 주식에 참여
- 이로 인해 급부상하는 키워드를 기반으로 투자하는 일명 '테마주' 투자가 많음
- 그렇다면 뉴스 데이터로 미리 테마를 파악할 수 있으면 수익을 기록하기 쉽지 않을까?

## Process
- '테마' 학습
  - 네이버 뉴스 크롤링 데이터 사용
  - '테마' 종류 리스트업
  - 각 테마에 대한 vector 학습
    - word2vec 사용
    
- 뉴스 기사별 테마 추츨
  - 네이버 뉴스 크롤링 데이터 사용
  - 기사 내 meaningeless contents 제거
  - 각 뉴스 기사별 vector 추출
  - 뉴스 기사별 vector와 테마별 vector를 비교
    - 코사인 유사도가 가장 높은 테마로 선정
    - 정확도를 위해 코사인 유사도 93% 이상인 뉴스만 추출
    
- Backtest
  - 뉴스 데이터에서 얻은 테마를 기반으로 backtest 진행
  - 2020.06.27 ~ 2020.07.02 기준 평균 수익률 2.23%
  - 연 단위 backtest (in progress)

- 자동화
  - In progress
