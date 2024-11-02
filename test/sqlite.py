import sqlite3

# 创建缓存数据库
def init_db(filename='cache.db'):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cache
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

# 写入缓存
def write_cache_db(key, value, filename='cache.db'):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# 读取缓存
def read_cache_db(key, filename='cache.db'):
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute("SELECT value FROM cache WHERE key=?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# 示例
init_db()
write_cache_db('key3', 'value3')
print(read_cache_db('key3'))