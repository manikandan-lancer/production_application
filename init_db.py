from database.connection import engine
from database.models import Base

print("Creating/Updating tables...")
Base.metadata.create_all(engine)
print("Done!")
