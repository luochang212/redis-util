import os
import json
import numpy as np
import redis
import redisearch

from sentence_transformers import SentenceTransformer


HF_ENDPOINT = 'https://hf-mirror.com'
DEFAULT_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
DEFAULT_MODEL_PATH = './all-MiniLM-L6-v2'


class RedisHandler:

    def __init__(self, host='localhost', port=6379, db=0):
        # create a redis client
        self.rc = redis.Redis(host=host, port=port, db=db)

    def ping(self):
        return self.rc.ping()

    def set(self, key, value):
        return self.rc.set(key, value)

    def set_with_expire(self, key, value, expire_time):
        ret = self.rc.set(key, value)
        if ret:
            return self.rc.expire(key, expire_time)
        else:
            return False

    def get(self, key):
        ret = self.rc.get(key)
        if ret:
            return ret.decode('utf-8')
        else:
            return ret

    def update(self, key, new_value):
        if self.rc.exists(key):
            return self.rc.set(key, new_value)
        else:
            return False

    def delete(self, key):
        return self.rc.delete(key)


class RediSearchHandler:

    def __init__(self,
                 name: str,
                 host: str = 'localhost',
                 port: int = 6379,
                 password: str = None):
        if password:
            self.rc = redisearch.Client(name, password=password, host=host, port=port)
        else:
            self.rc = redisearch.Client(name, host=host, port=port)

    def ping(self):
        self.rc.redis.ping()

    def set(self, key, value):
        return self.rc.redis.set(key, value)

    def get(self, key):
        return self.rc.redis.get(key)


class RedisIndexHandler:

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6379,
                 password: str = None):
        if password:
            self.rc = redis.Redis(host=host, port=port, password=password)
        else:
            self.rc = redis.Redis(host=host, port=port)

    def ping(self):
        self.rc.ping()

    def create_index(self, cmd):
        return self.rc.execute_command(*cmd)

    def delete_index(self, index_name):
        return self.rc.execute_command(f'FT.DROPINDEX {index_name} [DD]')

    def insert_index(self, key: str, data: dict):
        return self.rc.hset(key, mapping=data)

    def get_data(self, key: str):
        return self.rc.execute_command('HGETALL', key)

    def del_data(self, key: str):
        return self.rc.delete(key)

    def search_vector(self, query_vec, index_name, vector_field_name, num_return_vec):
        query_vec_binary = query_vec.tobytes()
        cmd = [
            'FT.SEARCH', index_name, f'*=>[KNN {num_return_vec} @{vector_field_name} $query_vec]', 
            'PARAMS', '2', 'query_vec', query_vec_binary, 'DIALECT', '2'
        ]
        return self.rc.execute_command(*cmd)


def gen_func(set_with_expire_func, expire_time):
    def func(*args, **kwargs):
        return set_with_expire_func(*args, **kwargs, expire_time=expire_time)
    return func


class VectorEngine:

    def __init__(self,
                 redis_client: RedisHandler,
                 expire_time: int = None,
                 model_name: str = DEFAULT_MODEL,
                 model_path: str = DEFAULT_MODEL_PATH,
                 hf_endpoint: str = DEFAULT_MODEL_PATH):
        # model env
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = model_path
        if hf_endpoint:
            os.environ['HF_ENDPOINT'] = hf_endpoint

        self.redis_client = redis_client
        self.expire_time = expire_time
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.cast = Cast()

        if expire_time:
            self.set_func = gen_func(self.redis_client.set_with_expire, expire_time)
        else:
            self.set_func = self.redis_client.set

    def ping(self):
        return self.redis_client.ping()

    def encode(self, doc) -> np.ndarray:
        return self.model.encode(doc)

    def get_and_set(self, doc) -> list:
        '''If the key does not exist, insert a new record'''
        v_str = self.redis_client.get(doc)
        if v_str:
            v = self.cast.str2list(v_str)
        else:
            v = self.encode(doc).tolist()
            v_str = self.cast.list2str(v)
            if not self.set_func(doc, v_str):
                print(f'fail to insert {doc}')

        return v

    def update(self, doc: str, embedding: list):
        embedding_str = self.cast.list2str(embedding)
        return self.redis_client.update(doc, embedding_str)

    def delete(self, doc):
        return self.redis_client.delete(doc)


class Cast:

    @staticmethod
    def list2str(lst: list):
        return json.dumps(lst)

    @staticmethod
    def str2list(s: str):
        return json.loads(s)


if __name__ == "__main__":
    rh = RedisHandler()

    print(f'rh.ping: {rh.ping()}')
    print(f'rh.set: {rh.set("a", "1")}')
    print(f'rh.set_with_expire: {rh.set_with_expire("b", "2", 10)}')
    print(f'rh.update: {rh.update("a", "3")}')
    print(f'rh.get: {rh.get("a").decode("utf-8")}')
