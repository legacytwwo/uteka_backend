from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID

############
def SQLAlchemyUUID(db):
  db.UUID = UUID
  return db
############
def uuid():
  return text('uuid_generate_v4()')
############
def timestamp():
  return text("(NOW() AT TIME ZONE 'UTC')")

def token(size = 30):
  ###########
  n = 30
  result = []
  result_sum = 0
  md5 = 'md5(random()::text)'
  ###########
  for i in range(1, size + 1):
    if(i % n == 0):
      result_sum += n
      result.append(n)
  ###########
  result_min = size - result_sum
  result.append(result_min) if result_min else None
  return text(f"concat({','.join(f'substr({md5},0,{str(x+1)})' for x in result)})")
############