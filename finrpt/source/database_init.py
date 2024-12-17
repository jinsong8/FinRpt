import sqlite3

COMPANY_INFO_TABLE_COLUMNS = ['stock_code', 'company_name', 'company_full_name', 'company_name_en', 'stock_category', 'industry_category', 'stock_exchange', 'industry_cs', 'general_manager', 'legal_representative', 'board_secretary', 'chairman', 'securities_representative', 'independent_directors', 'website', 'address', 'registered_capital', 'employees_number', 'management_number', 'company_profile', 'business_scope']
COMPANY_REPORT_TABLE_COLUMNS = ["report_id", "content", "stock_code", "date", "title", 'core_content', 'summary']


def company_info_table_init(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS company_info (
        stock_code TEXT PRIMARY KEY,
        company_name TEXT,
        company_full_name TEXT,
        company_name_en TEXT,
        stock_category TEXT,
        industry_category TEXT,
        stock_exchange TEXT,
        industry_cs TEXT,
        general_manager TEXT,
        legal_representative TEXT,
        board_secretary TEXT,
        chairman TEXT,
        securities_representative TEXT,
        independent_directors TEXT,
        website TEXT,
        address TEXT,
        registered_capital TEXT,
        employees_number TEXT,
        management_number TEXT,
        company_profile TEXT,
        business_scope TEXT
    )
    ''')
    conn.commit()
    conn.close()


def company_report_table_init(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS company_report (
        report_id TEXT PRIMARY KEY,
        content TEXT,
        stock_code TEXT,
        date TEXT,
        title TEXT,
        core_content TEXT,
        summary TEXT
    )
    ''')
    conn.commit()
    conn.close()


def company_news_table_init(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS news (
        news_url TEXT PRIMARY KEY,
        read_num TEXT,
        reply_num TEXT,
        news_title TEXT,
        news_author TEXT,
        news_time TEXT,
        stock_code TEXT,
        news_content TEXT,
        news_summary TEXT,
        dec_response TEXT,
        news_decision TEXT
    )
    ''')
    conn.commit()
    conn.close()


def announcement_table_init(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS announcement (
        url TEXT PRIMARY KEY,
        date TEXT,
        title TEXT,
        content TEXT,
        stock_code TEXT
    )
    ''')
    conn.commit()
    conn.close()