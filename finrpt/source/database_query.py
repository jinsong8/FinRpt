import sqlite3


def company_news_table_query_by_url(db, news_url):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        SELECT * FROM news WHERE news_url = ?
        ''', (news_url,))
        result = c.fetchone()
        conn.close()
        return result
    except Exception as e:
        if conn:
            conn.close()
        print(e)
        return None


def announcement_table_query_by_url(db, url):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        SELECT * FROM announcement WHERE url = ?
        ''', (url,))
        result = c.fetchone()
        conn.close()
        return result
    except Exception as e:
        if conn:
            conn.close()
        print(e)
        return None