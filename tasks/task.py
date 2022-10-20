from db import get_db
from models.core import Tasks
from models.core import TasksScheme
from contextlib import contextmanager

def db_add_task(task_name: str) -> TasksScheme:
  model = TasksScheme(task_name=task_name)
  scheme = db_update_task(model)
  return scheme

def db_update_task(model: TasksScheme) -> TasksScheme:
  with contextmanager(get_db)() as session:
    record = Tasks(**model.dict())
    record = session.merge(record)
    session.commit()
    scheme = TasksScheme.from_orm(record)
  return scheme

def db_get_tasks_by_id(tasks: list) -> TasksScheme:
  result = []
  with contextmanager(get_db)() as session:
    for task in tasks:
      scheme = TasksScheme
      query = session.query(Tasks)
      query = query.filter(Tasks.id == task).first()
      result.append(scheme.from_orm(query))
  return result