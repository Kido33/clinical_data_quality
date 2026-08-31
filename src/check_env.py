import os
from dotenv import load_dotenv

load_dotenv()

print("DB_USER:", repr(os.getenv("DB_USER")))
print("DB_HOST:", repr(os.getenv("DB_HOST")))
print("DB_PORT:", repr(os.getenv("DB_PORT")))
print("DB_NAME:", repr(os.getenv("DB_NAME")))
print("DB_PASSWORD exists:", bool(os.getenv("DB_PASSWORD")))