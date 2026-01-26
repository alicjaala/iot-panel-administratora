import sqlite3
import datetime
import sys, os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import raspberries.constants as const


def get_db_connection():
    conn = sqlite3.connect(const.DB_NAME)
    conn.row_factory = sqlite3.Row

    return conn


def allocate_or_retrieve_locker(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM entries WHERE uid = ? AND exit_tmsp IS NULL", (uid,))
        row = cursor.fetchone()

        if not row:
            return -1, False

        cursor.execute("SELECT nr FROM lockers WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        
        if row:
            return row['nr'], False
        
        cursor.execute("SELECT nr FROM lockers WHERE uid IS NULL LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            return None, False
        
        locker_nr = row['nr']
        
        cursor.execute("UPDATE lockers SET uid = ? WHERE nr = ?", (uid, locker_nr))

        cursor.execute("""
            UPDATE entries 
            SET locker_nr = ? 
            WHERE uid = ? AND exit_tmsp IS NULL
        """, (locker_nr, uid))
        
        conn.commit()
        return locker_nr, True

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return -1, False
    
    finally:
        conn.close()


def process_gate_event(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(1) as count FROM entries WHERE uid = ? AND exit_tmsp IS NULL", (uid,))
        is_inside = cursor.fetchone()['count'] > 0

        tmsp = datetime.datetime.now().replace(microsecond=0).isoformat(sep=" ")
        
        if is_inside:            
            cursor.execute("UPDATE entries SET exit_tmsp = ? WHERE uid = ? AND exit_tmsp IS NULL", (tmsp, uid))
            
            cursor.execute("UPDATE lockers SET uid = NULL WHERE uid = ?", (uid,))
            conn.commit()
            print(f"{uid} exit")
            return True

        else:
            cursor.execute("INSERT INTO entries (uid, entry_tmsp) VALUES (?, ?)", (uid, tmsp))
            conn.commit()
            print(f"{uid} enter")
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"Error processing gate: {e}")
        return False

    finally:
        conn.close()


def _get_all_helper(query):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        rows = cursor.execute(query).fetchall()
        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_all_lockers():
    return _get_all_helper("SELECT * FROM lockers")


def get_all_entries():
    return _get_all_helper("SELECT * FROM entries")


def force_release_locker(locker_nr):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT uid FROM lockers WHERE nr = ?", (locker_nr,))
        row = cursor.fetchone()
        
        if row and row['uid']:
            uid = row['uid']
            tmsp = datetime.datetime.now().replace(microsecond=0).isoformat(sep=" ")
            
            cursor.execute("""
                UPDATE entries 
                SET exit_tmsp = ? 
                WHERE uid = ? AND exit_tmsp IS NULL
            """, (tmsp, uid))
            
            cursor.execute("UPDATE lockers SET uid = NULL WHERE nr = ?", (locker_nr,))
            conn.commit()
            return True

        return False
    
    except Exception as e:
        conn.rollback()
        print(f"Error forcing release: {e}")
        return False

    finally:
        conn.close()
