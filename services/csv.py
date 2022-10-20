import csv
from oslash import Right
from datetime import datetime, timedelta

def get_csv(result) -> str:
  utc = datetime.utcnow()
  doc = open(f'files/{str(utc + timedelta(hours=3))}.csv', 'w', encoding='cp1251')
  writer = csv.writer(doc, delimiter=';')
  header = ['GUID', 'NAME', 'COUNTRY', 'PRODUCER', 'PRICE']
  writer.writerow(header)
  ind = -1
  for x in result:
    ind = ind + 1
    row = [x.guid, x.name, x.country, x.producer, x.price]
    try:
      writer.writerow(row)
    except UnicodeEncodeError:
      new_row = [str(item.encode('cp1251', 'ignore'), 'cp1251') if isinstance(item, str) else item for item in row]
      writer.writerow(new_row)
  doc.close()
  return Right(doc.name)