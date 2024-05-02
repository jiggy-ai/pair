from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    name: str
    age: Optional[int] = None

# Example instances
user_with_age = User(name="Alice", age=30)
user_without_age = User(name="Bob")

# Serialization
print(user_with_age.json())  # Outputs JSON with age
print(user_without_age.json(exclude_none=True))  # Outputs JSON without the age field