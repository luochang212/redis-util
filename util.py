import json
import redis
import redisearch


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
        if password is None:
            self.rc = redisearch.Client(name, host=host, port=port)
        else:
            self.rc = redisearch.Client(name, password=password, host=host, port=port)

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
        if password is None:
            self.rc = redis.Redis(host=host, port=port)
        else:
            self.rc = redis.Redis(host=host, port=port, password=password)

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
