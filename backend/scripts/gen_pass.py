import bcrypt

password = "admin123"
pwd_bytes = password.encode('utf-8')
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(pwd_bytes, salt)
print(hashed_password.decode('utf-8'))
