from app import app

@app.get("/api/ping", status_code=418)
def route_ping():
  return {'status': False}