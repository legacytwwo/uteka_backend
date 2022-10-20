import uvicorn
from app import app
from sys import argv
from routers.core import *

# pytest -vv -s --disable-warnings

# sudo service uteka.server stop
# sudo service uteka.server start
# sudo service uteka.server restart

# sudo service uteka.celery stop
# sudo service uteka.celery start
# sudo service uteka.celery restart

if __name__ == '__main__':
  port = 5701
  if len(argv) >= 2:
    if argv[1] == '--prod':
      port = 5700
  uvicorn.run('app:app', host="0.0.0.0", port=5700, reload=False)