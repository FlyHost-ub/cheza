import sqlite3

connection = sqlite3.connect('data.db')
q = connection.cursor()

def join(user):
    q.execute(f"SELECT * FROM users WHERE user_id = {user.id}")
    result = q.fetchall()
    if len(result) == 0:
        q.execute("INSERT INTO `users` (`user_id`, `user_name`, `user_username`, `balance`, `days`) VALUES (?, ?, ?, ?, ?)", (user.id, user.full_name, user.username, 0, 0))
        connection.commit()