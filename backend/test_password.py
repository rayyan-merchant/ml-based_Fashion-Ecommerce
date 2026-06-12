from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test password verification with the hash from the database
test_password = "rija1234"
rija_hash = "$2b$12$juvqkMFcf55SjsnYjEwaseO4IE3crWt7TiqIAxzlUcNTw9pr901KW"

result = pwd_context.verify(test_password, rija_hash)
print(f"Password 'rija1234' matches rija's hash: {result}")

# Test with other possible passwords
for pwd in ["rija", "rija123", "Rija1234", "RIJA1234"]:
    result = pwd_context.verify(pwd, rija_hash)
    print(f"Password '{pwd}' matches rija's hash: {result}")
