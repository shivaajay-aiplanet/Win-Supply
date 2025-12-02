"""Script to create the cross_reference table for LLM caching."""

import psycopg2

# Database connection string
POSTGRES_CONNECTION_STRING = (
    "postgresql://postgres:postgres@localhost:5432/win_supply_inv"
)


def create_cross_reference_table():
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor()

        # Check if table exists and has old schema
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'cross_reference' AND table_schema = 'public'
        """
        )
        existing_columns = [row[0] for row in cursor.fetchall()]

        if existing_columns and "wise_item_number" not in existing_columns:
            print("Found old schema, dropping and recreating table...")
            cursor.execute("DROP TABLE IF EXISTS public.cross_reference CASCADE")
            conn.commit()

        # Create cross_reference table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.cross_reference (
                id SERIAL PRIMARY KEY,
                wise_item_number VARCHAR(255) NOT NULL UNIQUE,
                llm_matches JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create index on wise_item_number for fast lookups
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cross_reference_wise_item_number 
            ON public.cross_reference(wise_item_number)
        """
        )

        conn.commit()
        print("✅ cross_reference table created successfully!")

        # Verify table structure
        cursor.execute(
            """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'cross_reference' AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        )

        print("\nTable structure:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]}")

        cursor.close()
        print("\n✅ Setup complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_cross_reference_table()
