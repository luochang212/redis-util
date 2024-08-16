import json
import redis


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
