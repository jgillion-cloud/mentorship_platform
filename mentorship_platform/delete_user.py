import sqlite3

# EXPLANATION: This script lets you delete users from the database
# It's safer than deleting directly because it shows you what will be deleted first

def list_users():
    """Show all users in the database"""
    # EXPLANATION: Connect to the database
    # This opens mentorship.db in read mode
    conn = sqlite3.connect('mentorship.db')
    conn.row_factory = sqlite3.Row  # Lets us access columns by name
    
    # Get all users
    users = conn.execute("SELECT id, email, user_type FROM users ORDER BY id").fetchall()
    
    print("\n=== All Users ===")
    print(f"{'ID':<5} {'Email':<40} {'Type':<15}")
    print("-" * 60)
    
    # EXPLANATION: Loop through each user and print their info
    # f"{'ID':<5}" means print "ID" left-aligned in 5 characters
    # This creates a nice table format
    for user in users:
        print(f"{user['id']:<5} {user['email']:<40} {user['user_type']:<15}")
    
    conn.close()
    print()  # Empty line for spacing

def delete_user(user_id):
    """Delete a user and all their related data"""
    conn = sqlite3.connect('mentorship.db')
    
    # EXPLANATION: First, check if user exists
    # This prevents errors if you try to delete non-existent users
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        print(f"No user found with ID {user_id}")
        conn.close()
        return
    
    print(f"\nDeleting user: {user[1]} (ID: {user_id})")
    
    # EXPLANATION: We need to delete in the right order
    # Because of foreign key constraints, we delete "child" records first
    # Then delete the "parent" record last
    
    # Step 1: Delete meetings associated with user's requests
    # EXPLANATION: This deletes meetings where the user was involved
    # Either as mentor (to_user_id) or student (from_user_id)
    conn.execute('''
        DELETE FROM meetings 
        WHERE request_id IN (
            SELECT id FROM requests 
            WHERE from_user_id = ? OR to_user_id = ?
        )
    ''', (user_id, user_id))
    print("  ✓ Deleted associated meetings")
    
    # Step 2: Delete requests sent by or to this user
    # EXPLANATION: Deletes all requests where user was sender or receiver
    conn.execute("DELETE FROM requests WHERE from_user_id = ? OR to_user_id = ?", 
                 (user_id, user_id))
    print("  ✓ Deleted associated requests")
    
    # Step 3: Delete college profile if exists
    # EXPLANATION: Only college students have profiles
    # This won't error if profile doesn't exist
    conn.execute("DELETE FROM college_profiles WHERE user_id = ?", (user_id,))
    print("  ✓ Deleted college profile (if existed)")
    
    # Step 4: Finally, delete the user
    # EXPLANATION: Now that all related data is gone, we can delete the user
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    print("  ✓ Deleted user account")
    
    # EXPLANATION: commit() saves all changes to the database
    # Without this, nothing would actually be deleted
    conn.commit()
    conn.close()
    
    print(f"\n✅ User {user_id} successfully deleted!\n")

# EXPLANATION: Main program logic
# This is what runs when you execute the script
if __name__ == "__main__":
    print("=" * 60)
    print("Tap In - User Deletion Tool")
    print("=" * 60)
    
    # Show all users first
    list_users()
    
    # Get user input
    # EXPLANATION: input() pauses and waits for user to type
    # We convert the input to an integer with int()
    try:
        user_id = input("Enter the ID of the user to delete (or 'q' to quit): ")
        
        if user_id.lower() == 'q':
            print("Exiting...")
            exit()
        
        # Convert to integer
        user_id = int(user_id)
        
        # Confirm deletion
        # EXPLANATION: This is a safety check
        # Forces user to type 'yes' to prevent accidental deletions
        confirm = input(f"Are you SURE you want to delete user {user_id}? Type 'yes' to confirm: ")
        
        if confirm.lower() == 'yes':
            delete_user(user_id)
        else:
            print("Deletion cancelled.")
    
    # EXPLANATION: Exception handling
    # Catches errors if user enters invalid input (like letters instead of numbers)
    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"Error: {e}")