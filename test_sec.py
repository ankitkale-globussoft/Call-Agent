from passlib.context import CryptContext
from jose import jwt

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    h = pwd_context.hash("test")
    print(f"Passlib works: {h[:10]}...")
    
    token = jwt.encode({"test": 1}, "secret", algorithm="HS256")
    print(f"Jose works: {token[:10]}...")
    
    print("Security libs are OK.")
except Exception as e:
    print(f"Security test failed: {e}")
