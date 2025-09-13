from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Annotated
from datetime import datetime
from uuid import uuid4, UUID
from statistics import mean
from collections import Counter
import json

app = FastAPI(title="Student Management System")


def load_data() -> List[dict]:
    try:
        with open("student.json", "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(students: List[dict]) -> None:
    with open("student.json", "w") as f:
        json.dump(students, f, indent=4, default=str) 



class Student(BaseModel):
    id: UUID
    name: Annotated[str, Field(min_length=2, description="Student Name Min 2 char")]
    email: EmailStr
    age: Annotated[int, Field(ge=10, le=100, description="Age must be between 10 and 100")]
    department: Optional[str] = None
    created_at: datetime
    CGPA: Annotated[int, Field(ge=0, le=4, description="CGPA must be between 0 and 4")]

    @field_validator("name")
    def validate_name(cls, value: str):
        if not value.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return value

class StudentCreate(BaseModel):
    name: Annotated[str, Field(min_length=2)]
    email: EmailStr
    age: Annotated[int, Field(ge=10, le=100)]
    department: Optional[str] = None
    CGPA: Annotated[int, Field(ge=0, le=4)]

class StudentUpdate(BaseModel):
    name: Optional[Annotated[str, Field(min_length=2)]] = None
    email: Optional[EmailStr] = None
    age: Optional[Annotated[int, Field(ge=10, le=100)]] = None
    department: Optional[str] = None
    CGPA: Optional[Annotated[int, Field(ge=0, le=4)]] = None


@app.get("/")
def home():
    return {"message": "FastAPI Student Management System is running!"}

@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: UUID):
    data = load_data()
    student = next((s for s in data if s["id"] == str(student_id)), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.get("/student_view")
def view_student():
    data = load_data()
    if not data:
        raise HTTPException(status_code=400, detail="No student exist")
    return data

@app.post("/students", response_model=Student)
def create_student(student: StudentCreate):
    try:
        data = load_data()

        if any(s["email"] == student.email for s in data):
            raise HTTPException(status_code=400, detail="Email already exists")

        new_student = Student(
            id=uuid4(),
            name=student.name,
            email=student.email,
            age=student.age,
            department=student.department,
            created_at=datetime.utcnow(),
            CGPA=student.CGPA
        )

        data.append(new_student.dict())
        save_data(data)
        return new_student
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
    
@app.put("/update_student/{stud_id}")
def Student_Update(stud_id: UUID, student: StudentUpdate):
    Data_Not_Changed = student.model_dump(exclude_unset=True)
    data = load_data()

    if any(s["email"] == student.email for s in data):
            raise HTTPException(status_code=400, detail="Email already exists")
  
    i = 0
    while i < len(data):
        if data[i]["id"] == str(stud_id): 
            
            for key, value in Data_Not_Changed.items():
                data[i][key] = value

            save_data(data)
            return {"message": "Successfully updated", "student": data[i]}
        i += 1

    raise HTTPException(status_code=404, detail="The given ID does not exist in the Json File")

@app.delete("/students/{student_id}")
def delete_student(student_id:UUID):
    data=load_data()
    i=0
    deleted=False
    while i < len(data):
        if data[i]["id"]==str(student_id):
            del data[i]
            deleted=True
            break
            i+=1
    
    if not deleted:
        raise HTTPException(status_code=404,detail="student not found")
    save_data(data)
    return {"message":"Student deleted Successfully"}

@app.get("/students",response_model=List[Student])
def list_students():
    return load_data()

@app.get("/students/search", response_model=List[Student])
def search_students(name: Optional[str] = None, email: Optional[str] = None):
    data = load_data()
    results = data

    if name:
     temp = []
     for stude in results:
        if name.lower() in stude["name"].lower():
            temp.append(stude)
     results = temp

    if email:
     temp = []
     for stude in results:
        if stude["email"].lower() == email.lower():
            temp.append(stude)
     results = temp
     return results
    
@app.get("/student/filter", response_model=List[Student])
def filter_students(department: str):
    data = load_data()
    results = []

    for stu in data:
        if stu.get("department", "").lower() == department.lower():
            results.append(stu)

    if not results:
        raise HTTPException(status_code=404, detail="No students found in this department")

    return results

@app.get("/students/sort", response_model=List[Student])
def sort_students(by: str = "age", order: str = "asc"):
    if by not in ("age", "name"):
        raise HTTPException(status_code=400, detail="Sort field must be 'age' or 'name'")
    if order not in ("asc", "desc"):
        raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")

    data = load_data()
    reverse = (order == "desc")
    data.sort(key=lambda s: s[by], reverse=reverse)
    return data

@app.get("/students/stats")
def student_stats():
    data = load_data()
    if not data:
        return {"total": 0, "average_age": None, "count_per_department": {}}
    total = len(data)
    avg_age = mean(s["age"] for s in data)
    dept_counts = Counter(s.get("department", "Unknown") for s in data)
    return {
        "total_students": total,
        "average_age": avg_age,
        "count_per_department": dept_counts
    }
      