"""Script to clear the cross_reference cache table."""
import psycopg2

POSTGRES_CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/win_supply_inv"

def clear_cache():
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Get count before clearing
        cursor.execute("SELECT COUNT(*) FROM public.cross_reference")
        count = cursor.fetchone()[0]
        
        # Clear the table
        cursor.execute("TRUNCATE TABLE public.cross_reference")
        conn.commit()
        
        print(f"✅ Cleared {count} cached entries from cross_reference table")
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_cache()

