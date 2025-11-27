from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


# def test_add_exam_acceptance():
#     res = client.post(
#         "/exams",
#         json={
#             "title": "Midterm",
#             "start_time": "10:00",
#             "end_time": "12:00",
#         },
#     )

#     assert res.status_code == 201
#     exam = res.json()

#     get_res = client.get(f"/exams/{exam['id']}")
#     assert get_res.status_code == 200
