import sqlite3
import pandas as pd


filename = "my.db"


def create_database() -> None:
    """Create a database and tables with sample data."""
    print("creating database...")
    conn = None
    try:
        conn = sqlite3.connect(filename)

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Clients(
                id INTEGER PRIMARY KEY NOT NULL,
                name TEXT,
                age INTEGER,
                goal TEXT,
                ram TEXT,
                needs_gpu TEXT
            )
        """
        )

        # Commit the changes
        conn.commit()
    except sqlite3.Error as e:
        print("create_database:", e)
    finally:
        if conn:
            conn.close()


def create_or_update_user(
    id: id,
    name: str = None,
    age: int = None,
    goal: str = None,
    ram: str = None,
    needs_gpu: str = None,
) -> None:
    """Create or update a user in the database."""
    conn = None
    try:
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()

        # Check if the user already exists
        cursor.execute("SELECT * FROM Clients WHERE id = ?", (id,))
        row = cursor.fetchone()

        if row:
            # If user exists, update the existing record
            sql_command = """
                UPDATE Clients
                SET name = COALESCE(?, name),
                    age = COALESCE(?, age),
                    goal = COALESCE(?, goal),
                    ram = COALESCE(?, ram),
                    needs_gpu = COALESCE(?, needs_gpu)
                WHERE id = ?
            """
            print(sql_command, id, name, age, goal, ram, needs_gpu)
            cursor.execute(sql_command, (name, age, goal, ram, needs_gpu, id))
        else:
            # If user doesn't exist, create a new record
            cursor.execute(
                """
                INSERT INTO Clients (id, name, age, goal, ram, needs_gpu)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (id, name, age, goal, ram, needs_gpu),
            )

        # Commit the changes
        conn.commit()

    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def get_user_by_id(id: int) -> pd.DataFrame:
    """Fetch user information by id and return as a pandas DataFrame."""
    conn = None
    try:
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()

        # Execute query to get the user by id
        cursor.execute("SELECT * FROM Clients WHERE id = ?", (id,))
        row = cursor.fetchone()

        if row:
            # Get column names for the DataFrame
            columns = [description[0] for description in cursor.description]

            # Create a pandas DataFrame with the row data
            df = pd.DataFrame([row], columns=columns)
            df = df.rename(
                {
                    "name": "Client Name",
                    "age": "Age",
                    "ram": "RAM",
                    "goal": "Goal",
                    "needs_gpu": "GPU",
                },
                axis=1,
            )
            return df
        else:
            print(f"No user found with id {id}")
            # Return an empty DataFrame if no user found
            return pd.DataFrame(
                columns=["Client Name", "Age", "RAM", "Goal", "Memory", "GPU"]
            )
    except sqlite3.Error:
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def delete_user_by_id(id: int) -> True:
    """Delete user by ."""
    conn = None
    response = True
    try:
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()

        # Execute query to get the user by id
        sql_command = "DELETE FROM Clients WHERE id = ?"

        # Execute query to delete the user by id
        cursor.execute(sql_command, (id,))

        # Commit the transaction
        conn.commit()
    except sqlite3.Error:
        response = False
    finally:
        if conn:
            conn.close()

    return response
