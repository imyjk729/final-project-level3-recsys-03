from google.oauth2 import service_account
from google.cloud import bigquery

cd = service_account.Credentials.from_service_account_file('/opt/ml/clear-shell-351201-702c702ea7fc.json')
project_id = 'clear-shell-351201'

bq = bigquery.Client(project=project_id, credentials = cd)

def load_train_data():
    """
    bigquery에 저장되어있는 articles테이블을 기반으로 articles.csv로 데이터를 로드하는 함수
    
    """
    query = """
		SELECT  * FROM `clear-shell-351201.musinsadb.articles`;
    """
    df = bq.query(query).to_dataframe() 
    df.to_csv('/opt/ml/musinsa_dataset/data/articles.csv', index=False,header=True)
    print('csv file generated')

def load_to_bigquery(result,destination_table):
    """
    result를 bigquery에 저장하는 함수
    
    Parameters:
    result(dtype=dataframe): bigquery에 저장할 dataframe
    destination(dtype=string): bigquery 테이블 이름
    
    Returns:
    None
    """
    result.to_gbq(destination_table, project_id, if_exists='replace',credentials=cd)
    print(
            f"csv uploaded to {destination_table}."
        )

def load_features_to_bigquery(result,destination_table):
    """
    bigquery에 저장된 테이블을 cosine similarity계산할수있는 형태로 변경하는 함수
    
    Parameters:
    result(dtype=dataframe): bigquery에 저장할 dataframe
    destination(dtype=string): bigquery 테이블 이름
    
    Returns:
    None
    """

    load_to_bigquery(result,destination_table)

    query = """
        CREATE OR REPLACE TABLE `clear-shell-351201.musinsadb.img_features`
        AS
        SELECT
        path,
        (
        SELECT ARRAY_AGG(CAST(v as FLOAT64) ORDER BY o asc)
        FROM UNNEST(SPLIT(REGEXP_EXTRACT(features, r"^\[(.*)\]$"), ", ")) v WITH OFFSET o
        ) AS features
        FROM `clear-shell-351201.musinsadb.img_features`
    """
    job = bq.query(query)    
    print(
            f"features uploaded to {destination_table}."
        )


def load_search_feature_to_bigquery(result,destination_table):
    """
    bigquery에 저장된 테이블을 cosine similarity계산할수있는 형태로 변경하는 함수
    
    Parameters:
    result(dtype=dataframe): bigquery에 저장할 dataframe
    destination(dtype=string): bigquery 테이블 이름
    
    Returns:
    None
    """
    load_to_bigquery(result,destination_table)

    query = """
        CREATE OR REPLACE TABLE `clear-shell-351201.musinsadb.target`
        AS
        SELECT
        path,
        (
        SELECT ARRAY_AGG(CAST(v as FLOAT64) ORDER BY o asc)
        FROM UNNEST(SPLIT(REGEXP_EXTRACT(features, r"^\[(.*)\]$"), ", ")) v WITH OFFSET o
        ) AS features
        FROM `clear-shell-351201.musinsadb.target`
    """
    job = bq.query(query)    
    print(
            f"features uploaded to {destination_table}."
        )


def cal_similarity():
    """
    cosine similarity계산하는 query를 bigquery에 전달하는 함수
    
    Returns:
    df(dtype=dataframe): cosine similarity계산된 dataframe

    """
    query = """
        SELECT key1, key2, ( 
        SELECT 
            SUM(value1 * value2)/ 
            SQRT(SUM(value1 * value1))/ 
            SQRT(SUM(value2 * value2))
        FROM UNNEST(nt.f1) value1 WITH OFFSET pos1 
        JOIN UNNEST(nt.f2) value2 WITH OFFSET pos2 
        ON pos1 = pos2 ) cosine_similarity
        FROM `musinsadb.newtable` AS nt
        ORDER BY cosine_similarity
        DESC
    """
    job = bq.query(query)
    df = job.to_dataframe()
    
    return df


def creat_union_table():
    query = """
        CREATE OR REPLACE TABLE `clear-shell-351201.musinsadb.newtable`
        AS SELECT
            t1.path AS key1, t1.features AS f1,
            t2.path AS key2, t2.features AS f2 as FLOAT64,
            
        FROM
            musinsadb.img_features AS t1,
            musinsadb.target AS t2
    """

    job = bq.query(query)    
    print(
            "created table ..."
        )


