from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, constr
from typing import Optional, List
from enum import Enum
from datetime import datetime, timedelta

app = FastAPI()

class TaskStatus(str, Enum):
    todo = "TODO"
    in_progress = "W TRAKCIE"
    done = "ZAKOŃCZONE"

class Task(BaseModel):
    id: int
    title: constr(min_length=3, max_length=100)
    description: Optional[constr(max_length=300)] = None
    status: TaskStatus = TaskStatus.todo

class TaskCreate(BaseModel):
    title: constr(min_length=3, max_length=100)
    description: Optional[constr(max_length=300)] = None
    status: Optional[TaskStatus] = TaskStatus.todo

class TaskUpdate(BaseModel):
    title: Optional[constr(min_length=3, max_length=100)] = None
    description: Optional[constr(max_length=300)] = None
    status: Optional[TaskStatus] = None

class PomodoroTimer(BaseModel):
    task_id: int
    duration: int = 25

class StopPomodoro(BaseModel):
    task_id: int

tasks = [
    {
        "id": 1,
        "title": "Nauka FastAPI",
        "description": "Przygotować przykładowe API z dokumentacją",
        "status": "TODO",
    }
]

pomodoro_sessions = [
    {
        "task_id": 1,
        "start_time": "2025-01-09T12:00:00",
        "end_time": "2025-01-09T12:25:00",
        "completed": True,
    }
]

@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    for existing_task in tasks:
        if existing_task["title"] == task.title:
            raise HTTPException(status_code=400, detail="Tytuł musi być unikalny.")
    
    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
    }
    tasks.append(new_task)
    return new_task

@app.get("/tasks", response_model=List[Task])
def get_tasks(status: Optional[TaskStatus] = Query(None)):
    if status:
        return [task for task in tasks if task["status"] == status.value]
    return tasks

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if task_update.title:
                for existing_task in tasks:
                    if existing_task["title"] == task_update.title and existing_task["id"] != task_id:
                        raise HTTPException(status_code=400, detail="Tytuł musi być unikalny.")
            if task_update.title:
                task["title"] = task_update.title
            if task_update.description:
                task["description"] = task_update.description
            if task_update.status:
                task["status"] = task_update.status.value
            return task
    raise HTTPException(status_code=404, detail="Zadanie o podanym ID nie istnieje.")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return {"message": "Zadanie zostało usunięte."}
    raise HTTPException(status_code=404, detail="Zadanie o podanym ID nie istnieje.")

@app.post("/pomodoro", response_model=dict)
def create_pomodoro(pomodoro: PomodoroTimer):
    task_exists = any(task["id"] == pomodoro.task_id for task in tasks)
    if not task_exists:
        raise HTTPException(status_code=404, detail="Zadanie o podanym ID nie istnieje.")
    
    existing_session = next((session for session in pomodoro_sessions if session["task_id"] == pomodoro.task_id and not session["completed"]), None)
    if existing_session:
        raise HTTPException(status_code=400, detail="Zadanie już ma aktywny timer Pomodoro.")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=pomodoro.duration)
    pomodoro_sessions.append({
        "task_id": pomodoro.task_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "completed": False
    })
    return {"message": f"Pomodoro timer dla zadania ID {pomodoro.task_id} został ustawiony na {pomodoro.duration} minut."}

@app.post("/pomodoro/{task_id}/stop", response_model=dict)
def stop_pomodoro(task_id: int):
    task_exists = any(task["id"] == task_id for task in tasks)
    if not task_exists:
        raise HTTPException(status_code=404, detail="Zadanie o podanym ID nie istnieje.")
    
    active_session = next((session for session in pomodoro_sessions if session["task_id"] == task_id and not session["completed"]), None)
    if not active_session:
        raise HTTPException(status_code=400, detail="Nie ma aktywnego timera Pomodoro dla tego zadania.")
    
    active_session["completed"] = True
    return {"message": f"Timer Pomodoro dla zadania ID {task_id} został zatrzymany."}

@app.get("/pomodoro/stats", response_model=dict)
def get_pomodoro_stats():
    stats = {}
    for task in tasks:
        task_id = task["id"]
        completed_sessions = [session for session in pomodoro_sessions if session["task_id"] == task_id and session["completed"]]
        total_time = len(completed_sessions) * 25
        stats[task_id] = {"sessions": len(completed_sessions), "total_time": total_time}
    return stats
