def get_secret_key():
    with open('key.txt', 'r') as secret_key:
        return secret_key.read().strip()
    
def get_password_hash():
    with open('secret.txt', 'r') as password_hash:
        return password_hash.read().strip()