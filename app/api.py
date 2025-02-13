from flask import Blueprint, jsonify
import psycopg2

api_bp = Blueprint('api_bp', __name__)  # ประกาศ Blueprint

def get_db_connection():
    """เชื่อมต่อฐานข้อมูล PostgreSQL"""
    return psycopg2.connect(
        dbname="postgres",    
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )

@api_bp.route('/employee/<emp_id>', methods=['GET'])
def get_employee(emp_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) ตรวจสอบว่ามี emp_id ในตาราง employees หรือไม่
    cur.execute("""
        SELECT emp_id, department 
        FROM employees 
        WHERE emp_id = %s
    """, (emp_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "Employee not found"}), 404

    # สร้างโครงสร้าง JSON ของพนักงาน
    employee_data = {
        "emp_id": row[0],
        "department": row[1],
        "missions": []
    }

    # 2) ดึง missions ที่เชื่อมโยงกับ emp_id
    cur.execute("""
        SELECT id, mission_name 
        FROM missions 
        WHERE emp_id = %s
    """, (emp_id,))
    mission_rows = cur.fetchall()

    for mission_row in mission_rows:
        mission_id, mission_name = mission_row
        mission_dict = {
            "mission_id": mission_id,
            "mission_name": mission_name,
            "kpis": []
        }

        # 3) ดึง kpis สำหรับ mission นี้
        cur.execute("""
            SELECT id, kpi_name, kpi_category
            FROM kpis 
            WHERE mission_id = %s
        """, (mission_id,))
        kpi_rows = cur.fetchall()

        for kpi_row in kpi_rows:
            kpi_id, kpi_name, kpi_category = kpi_row
            kpi_dict = {
                "kpi_id": kpi_id,
                "kpi_name": kpi_name,
                "kpi_category": kpi_category,
                "definitions": []
            }

            # 4) ดึง definitions ที่เชื่อมโยงกับ KPI นี้
            cur.execute("""
                SELECT DISTINCT d.id, d.definition_text, d.weight, d.score
                FROM definitions d
                JOIN kpis k ON d.kpi_id = k.id
                JOIN missions m ON k.mission_id = m.id
                WHERE k.id = %s AND m.id = %s AND m.emp_id = %s
            """, (kpi_id, mission_id, emp_id))
            definition_rows = cur.fetchall()

            for drow in definition_rows:
                definition_id, definition_text, weight, score = drow
                def_dict = {
                    "definition_id": definition_id,
                    "definition_text": definition_text,
                    "weight": weight,
                    "score": score
                }
                kpi_dict["definitions"].append(def_dict)

            mission_dict["kpis"].append(kpi_dict)

        employee_data["missions"].append(mission_dict)

    cur.close()
    conn.close()
    return jsonify(employee_data), 200
