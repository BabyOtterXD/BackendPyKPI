from flask import Blueprint, request, jsonify
import requests
from app.backend import get_db_connection
from psycopg2.extras import RealDictCursor

user_bp = Blueprint('user', __name__)

def fetch_users_in_batches(api_url, token, skip=0, take=1000):
    while True:
        url = f"{api_url}?skip={skip}&take={take}"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        print(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            yield None
            return

        response_json = response.json()
        # ตรวจสอบรูปแบบข้อมูลที่ได้ว่าเป็น list หรือ dictionary
        if isinstance(response_json, dict):
            batch = response_json.get("data", [])
        elif isinstance(response_json, list):
            batch = response_json
        else:
            batch = []

        if not batch or len(batch) == 0:
            break

        yield batch

        if len(batch) < take:
            break

        skip += take

def save_users_to_db(users):
    """
    บันทึกรายชื่อผู้ใช้ (users) ลงในตาราง Users โดยเลือกเฉพาะ attribute ที่ต้องการ
    เช่น userId, username, titleTH, dob, age
    """
    if not users:
        return 0
    total_saved = 0
    
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                for user in users:
                    # หาก API ส่ง userId มา เราสามารถใช้ค่านั้นได้ หรือปล่อยให้ DB สร้างเอง
                    user_id = user.get("userId")  # ตัวอย่าง: "000e1b56-8da2-4bfd-800f-4e0fdee5d1ae"
                    username = user.get("username")
                    titleTH = user.get("titleTH")
                    firstNameTH = user.get("firstNameTH")
                    lastNameTH = user.get("lastNameTH")
                    firstNameEN = user.get("firstNameEN")
                    lastNameEN = user.get("lastNameEN")
                    dob = user.get("dob")
                    
                    # หากมี user_id ให้ระบุค่านั้นลงไปด้วย หากไม่มีให้ปล่อยว่างเพื่อให้ DB สร้าง uuid ใหม่
                    if user_id:
                        cur.execute("""
                            INSERT INTO Users (id, username, titleTH, dob, firstNameTH, lastNameTH, firstNameEN, lastNameEN)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (user_id, username, titleTH, dob, firstNameTH, lastNameTH, firstNameEN, lastNameEN))
                    else:
                        cur.execute("""
                            INSERT INTO Users (username, titleTH, dob, firstNameTH, lastNameTH, firstNameEN, lastNameEN)
                            VALUES (%s, %s, %ss, %s, %s, %s, %s)
                        """, (username, titleTH, dob, firstNameTH, lastNameTH, firstNameEN, lastNameEN))
                    total_saved += 1
        conn.commit()
    except Exception as e:
        print("Error saving users:", e)
    finally:
        conn.close()
    return total_saved

@user_bp.route('/user/fetch-and-save-batch', methods=['GET'])
def fetch_and_save_user_batches():
    """
    Endpoint สำหรับดึงข้อมูลผู้ใช้ทีละ batch (skip/take) จาก API แล้วบันทึกลง DB
    """
    # กำหนดค่า token ให้ถูกต้องตามที่ API ต้องการ (ถ้าจำเป็น)
    token = ".eyJzc29DbGllbnQiOnsic3NvQ2xpZW50SWQiOiIzMTc3ZTUzZS02ODY0LTQ3MTAtYmY5OS01MGY3ZGI1OWJlYmIiLCJuYW1lIjoiSU1fQkFDS19PRkZJQ0UiLCJsb2dvVVJJIjpudWxsLCJyZWRpcmVjdFVSSSI6bnVsbCwiY2xpZW50SWQiOiJJTV9CQUNLX09GRklDRSJ9LCJ1c2VyIjp7InVzZXJJZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsImRpc3BsYXlOYW1lIjoiS0FSSVMxNDEyIiwic3RhZmZzIjpbeyJzdGFmZklkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIiwiZW1wbG95ZWVJZCI6IjAwMDAwIn1dLCJpc0ltcGFjdEVtcGxveWVlIjp0cnVlLCJpc0FkbWluIjp0cnVlLCJ1c2VyR3JvdXBzIjpbeyJ1c2VyR3JvdXBJZCI6IjE2ZGNmYzRhLWNjOTgtNDVjNC04MDgxLTNmMmVmYzQyOTZmNSIsImdyb3VwSWQiOiJJTV9DSEFMTEVOR0VSIiwidXNlcklkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIiwiaW50ZXJuYWxSb2xlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDI0LTA0LTIyVDAzOjAzOjM0LjE3MVoiLCJ1cGRhdGVkQXQiOiIyMDI0LTA0LTIyVDAzOjAzOjM0LjE3MVoiLCJncm91cCI6eyJncm91cElkIjoiSU1fQ0hBTExFTkdFUiIsIm5hbWUiOiJJTSBDaGFsbGVuZ2VyIiwiZGVzY3JpcHRpb24iOiJJTSBDaGFsbGVuZ2VyIiwicm9sZSI6IkdFTkVSQUwiLCJjcmVhdGVkQXQiOiIyMDIzLTA4LTIyVDAyOjQ0OjM5Ljg1MFoiLCJ1cGRhdGVkQXQiOiIyMDIzLTA4LTIyVDAyOjQ0OjM5Ljg1MFoifX0seyJ1c2VyR3JvdXBJZCI6IjdkZmNmOGYxLTRiYTktNGFhOC1iOWIzLTFjZjk4ODc1Yjg2YSIsImdyb3VwSWQiOiJNU01fU01BUlRZX1VTRVIiLCJ1c2VySWQiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDAiLCJpbnRlcm5hbFJvbGUiOm51bGwsImNyZWF0ZWRBdCI6IjIwMjMtMTItMDZUMDY6MDg6NDIuMDExWiIsInVwZGF0ZWRBdCI6IjIwMjMtMTItMDZUMDY6MDg6NDIuMDExWiIsImdyb3VwIjp7Imdyb3VwSWQiOiJNU01fU01BUlRZX1VTRVIiLCJuYW1lIjoiTVNNIFNtYXJ0eSBVc2VyIiwiZGVzY3JpcHRpb24iOiJNU00gU21hcnR5IFVzZXIiLCJyb2xlIjoiR0VORVJBTCIsImNyZWF0ZWRBdCI6IjIwMjMtMDgtMDRUMDU6NDI6NTkuMTQwWiIsInVwZGF0ZWRBdCI6IjIwMjMtMDgtMDRUMDU6NDI6NTkuMTQwWiJ9fSx7InVzZXJHcm91cElkIjoiOTk0Y2JhNzYtYzRmZS00MTE0LWI0MTctNTU5NWE1NjdhYzQ5IiwiZ3JvdXBJZCI6IlNVUEVSX0FETUlOIiwidXNlcklkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIiwiaW50ZXJuYWxSb2xlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDIzLTA5LTI2VDAyOjMxOjMzLjM3OVoiLCJ1cGRhdGVkQXQiOiIyMDIzLTA5LTI2VDAyOjMxOjMzLjM3OVoiLCJncm91cCI6eyJncm91cElkIjoiU1VQRVJfQURNSU4iLCJuYW1lIjoiU3VwZXJBZG1pbiIsImRlc2NyaXB0aW9uIjoiQWxsb3cgQWxsIFBlcm1pc3Npb25zIiwicm9sZSI6IlNVUEVSX0FETUlOIiwiY3JlYXRlZEF0IjoiMjAyMy0wNS0xMVQwOTo1MjowNS43NzVaIiwidXBkYXRlZEF0IjoiMjAyMy0wNS0xMVQwOTo1MjowNS43NzVaIn19LHsidXNlckdyb3VwSWQiOiJjODJkMDM1ZS02OGMwLTQ1ZWEtOTRlMC03MDZlOGExZWVjODMiLCJncm91cElkIjoiTVNNX0FDQ09VTlRJTkdfQURNSU4iLCJ1c2VySWQiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDAiLCJpbnRlcm5hbFJvbGUiOiIxIiwiY3JlYXRlZEF0IjoiMjAyNC0wNS0wNVQwNDowNDozMC43NjdaIiwidXBkYXRlZEF0IjoiMjAyNC0wNS0wNVQwNDowNjowMC4yMzNaIiwiZ3JvdXAiOnsiZ3JvdXBJZCI6Ik1TTV9BQ0NPVU5USU5HX0FETUlOIiwibmFtZSI6Ik1TTSBBY2NvdW50aW5nIEFkbWluIiwiZGVzY3JpcHRpb24iOiJNU00gQWNjb3VudGluZyBBZG1pbiIsInJvbGUiOiJHRU5FUkFMIiwiY3JlYXRlZEF0IjoiMjAyMy0wOC0wNFQwNTo0MzoxMC4xOTJaIiwidXBkYXRlZEF0IjoiMjAyMy0wOC0wNFQwNTo0MzoxMC4xOTJaIn19LHsidXNlckdyb3VwSWQiOiJkYmM3ZDBiMC1hZmRhLTQ5MDMtYjFjYi1jMjEyMDJmNmI0YTkiLCJncm91cElkIjoiVEVTVEVSIiwidXNlcklkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIiwiaW50ZXJuYWxSb2xlIjpudWxsLCJjcmVhdGVkQXQiOiIyMDIzLTEyLTIxVDE1OjQ1OjU2Ljg0NVoiLCJ1cGRhdGVkQXQiOiIyMDIzLTEyLTIxVDE1OjQ1OjU2Ljg0NVoiLCJncm91cCI6eyJncm91cElkIjoiVEVTVEVSIiwibmFtZSI6IlRlc3RlciIsImRlc2NyaXB0aW9uIjoiVGVzdGVyIiwicm9sZSI6IkdFTkVSQUwiLCJjcmVhdGVkQXQiOiIyMDIzLTEyLTA4VDExOjUyOjA2LjE2MVoiLCJ1cGRhdGVkQXQiOiIyMDIzLTEyLTA4VDExOjUyOjA2LjE2MVoifX1dfSwiYWNjZXNzVG9rZW5FeHBpcmVkT24iOiIyMDI0LTA5LTA0VDA5OjExOjAyLjM2OVoiLCJpYXQiOjE3MTc2NjUwNjJ9.eVgz6QDJgNpUqhf2YV61n79fZkA20A2i4iuBywuyNf4"
    api_url = "https://im-sso-staging.hr-impact.co/users"
    
    total_saved = 0

    # วนลูปดึงข้อมูลทีละ batch
    for batch in fetch_users_in_batches(api_url, token, skip=0, take=1000):
        if batch is None:
            # หมายถึงเกิดข้อผิดพลาดขณะดึงข้อมูล (response.status_code != 200)
            return jsonify({"status": "error", "message": "Error fetching data from API."}), 400
        
        # บันทึกข้อมูลใน batch ลงในฐานข้อมูล
        saved_count = save_users_to_db(batch)
        total_saved += saved_count
        print(f"Batch saved: {saved_count} users.")

    return jsonify({"status": "success", "message": f"Fetched and saved {total_saved} users."}), 200

@user_bp.route('/users', methods=['GET'])
def get_all_users():
    """
    Endpoint สำหรับดึงข้อมูลผู้ใช้ทั้งหมดจากฐานข้อมูล โดยรวมข้อมูล firstNameTH, lastNameTH, firstNameEN, lastNameEN
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, firstNameTH, lastNameTH, firstNameEN, lastNameEN, titleTH, dob 
                FROM Users 
                ORDER BY id ASC
            """)
            rows = cur.fetchall()
            # แปลงผลลัพธ์เป็น list ของ dict โดยใช้ชื่อคอลัมน์
            columns = [desc[0] for desc in cur.description]
            users = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print("Error fetching users:", e)
        return jsonify({"status": "error", "message": "Error fetching users from DB."}), 500
    finally:
        conn.close()
    return jsonify({"status": "success", "data": users}), 200