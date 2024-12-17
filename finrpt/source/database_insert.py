import sqlite3


def company_info_table_insert_em(db, data, stock_code):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
            INSERT INTO company_info (
                stock_code, company_name, company_full_name, company_name_en, stock_category,
                industry_category, stock_exchange, industry_cs, general_manager, legal_representative,
                board_secretary, chairman, securities_representative, independent_directors, website,
                address, registered_capital, employees_number, management_number, company_profile, business_scope
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stock_code,
            data.get('SECURITY_NAME_ABBR'),
            data.get('ORG_NAME'),
            data.get('ORG_NAME_EN'),
            data.get('SECURITY_TYPE'),
            data.get('EM2016'),
            data.get('TRADE_MARKET'),
            data.get('INDUSTRYCSRC1'),
            data.get('PRESIDENT'),
            data.get('LEGAL_PERSON'),
            data.get('SECRETARY'),
            data.get('CHAIRMAN'),
            data.get('SECPRESENT'),
            data.get('INDEDIRECTORS'),
            data.get('ORG_WEB'),
            data.get('ADDRESS'),
            data.get('REG_CAPITAL'),
            data.get('EMP_NUM'),
            data.get('TATOLNUMBER'),
            data.get('ORG_PROFILE'),
            data.get('BUSINESS_SCOPE')
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()
            return True
    return False


def company_report_table_insert(db, data):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        INSERT INTO company_report (
        report_id, content, stock_code, date, title, core_content, summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('report_id'),
            data.get('content'),
            data.get('stock_code'),
            data.get('date'),
            data.get('title'),
            data.get('core_content'),
            data.get('summary')
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if conn:
            conn.close()
        print(e)
        return False
    

def company_news_table_insert(db, data):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        INSERT INTO news (
            news_url, read_num, reply_num, news_title, news_author, news_time, stock_code, news_content, news_summary, dec_response, news_decision
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        data.get('news_url'),
        data.get('read_num'),
        data.get('reply_num'),
        data.get('news_title'),
        data.get('news_author'),
        data.get('news_time'),
        data.get('stock_code'),
        data.get('news_content'),
        data.get('news_summary'),
        data.get('dec_response'),
        data.get('news_decision'),
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if conn:
            conn.close()
        print(e)
        return False
    

import sqlite3

def announcement_table_insert(db, data):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute('''
        INSERT INTO announcement (
            url, date, title, content, stock_code
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
        data.get('url'),
        data.get('date'),
        data.get('title'),
        data.get('content'),
        data.get('stock_code')
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        if conn:
            conn.close()
        print(e)
        return False
