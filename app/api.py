from flask import Blueprint, jsonify, request
import psycopg2

api_bp = Blueprint('api_bp', __name__)

def get_db_connection():
    """เชื่อมต่อกับฐานข้อมูล PostgreSQL"""
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )

# ---------------------------
# 1. ดึงข้อมูลพนักงานรายบุคคล (ใช้ emp_id)
# ---------------------------
@api_bp.route('/employee/single', methods=['GET'])
def get_employee_by_id():
    emp_id = request.args.get('emp_id')
    if not emp_id:
        return jsonify({"error": "emp_id parameter is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
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

    employee_data = {
        "emp_id": row[0],
        "department": row[1],
        "missions": []
    }

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

# ---------------------------
# 2. ดึงข้อมูลพนักงานทั้งหมด
# ---------------------------
@api_bp.route('/employee/all', methods=['GET'])
def get_all_employees():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT emp_id, department FROM employees")
    employees_rows = cur.fetchall()
    
    employees_list = []
    for emp_row in employees_rows:
        emp_id, department = emp_row
        employee_data = {
            "emp_id": emp_id,
            "department": department,
            "missions": []
        }
        cur.execute("SELECT id, mission_name FROM missions WHERE emp_id = %s", (emp_id,))
        mission_rows = cur.fetchall()
        for mission_row in mission_rows:
            mission_id, mission_name = mission_row
            mission_dict = {
                "mission_id": mission_id,
                "mission_name": mission_name,
                "kpis": []
            }
            cur.execute("SELECT id, kpi_name, kpi_category FROM kpis WHERE mission_id = %s", (mission_id,))
            kpi_rows = cur.fetchall()
            for kpi_row in kpi_rows:
                kpi_id, kpi_name, kpi_category = kpi_row
                kpi_dict = {
                    "kpi_id": kpi_id,
                    "kpi_name": kpi_name,
                    "kpi_category": kpi_category,
                    "definitions": []
                }
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
        employees_list.append(employee_data)
    cur.close()
    conn.close()
    return jsonify(employees_list), 200

# ---------------------------
# 3. ดึงข้อมูลพนักงานโดยกรอง KPI ตาม kpi_category
# ---------------------------
@api_bp.route('/kpi', methods=['GET'])
def get_employees_by_kpi_category_query():
    # รับค่า kpi_category จาก query parameter
    kpi_category = request.args.get('kpi_category')
    if not kpi_category:
        return jsonify({"error": "kpi_category parameter is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # ดึงข้อมูลพนักงานทั้งหมด
    cur.execute("SELECT emp_id, department FROM employees")
    employees_rows = cur.fetchall()

    result = []
    for emp_row in employees_rows:
        emp_id, department = emp_row
        employee_data = {
            "emp_id": emp_id,
            "department": department,
            "missions": []
        }
        # ดึง missions สำหรับพนักงานนี้
        cur.execute("SELECT id, mission_name FROM missions WHERE emp_id = %s", (emp_id,))
        mission_rows = cur.fetchall()
        for mission_row in mission_rows:
            mission_id, mission_name = mission_row
            mission_dict = {
                "mission_id": mission_id,
                "mission_name": mission_name,
                "kpis": []
            }
            # ดึง kpis สำหรับ mission นี้
            cur.execute("SELECT id, kpi_name, kpi_category FROM kpis WHERE mission_id = %s", (mission_id,))
            kpi_rows = cur.fetchall()
            for kpi_row in kpi_rows:
                kpi_id, kpi_name, kpi_cat = kpi_row
                # กรอง KPI ตาม kpi_category ที่ส่งเข้ามา
                if kpi_cat != kpi_category:
                    continue
                kpi_dict = {
                    "kpi_id": kpi_id,
                    "kpi_name": kpi_name,
                    "kpi_category": kpi_cat,
                    "definitions": []
                }
                # ดึง definitions สำหรับ KPI นี้
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
                if kpi_dict["definitions"]:
                    mission_dict["kpis"].append(kpi_dict)
            if mission_dict["kpis"]:
                employee_data["missions"].append(mission_dict)
        if employee_data["missions"]:
            result.append(employee_data)

    cur.close()
    conn.close()
    return jsonify(result), 200

@api_bp.route('/employee/department', methods=['GET'])
def get_employees_by_department():
    # รับค่า department จาก query parameter
    department_filter = request.args.get('department')
    if not department_filter:
        return jsonify({"error": "department parameter is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # ดึงข้อมูลพนักงานที่มี department ตรงกับค่า department_filter
    cur.execute("""
        SELECT emp_id, department
        FROM employees
        WHERE department = %s
    """, (department_filter,))
    employees_rows = cur.fetchall()

    if not employees_rows:
        cur.close()
        conn.close()
        return jsonify({"error": f"No employee found for department: {department_filter}"}), 404

    employees_list = []
    for emp_row in employees_rows:
        emp_id, dept = emp_row
        employee_data = {
            "emp_id": emp_id,
            "department": dept,
            "missions": []
        }
        # ดึง missions สำหรับพนักงานนี้
        cur.execute("SELECT id, mission_name FROM missions WHERE emp_id = %s", (emp_id,))
        mission_rows = cur.fetchall()
        for mission_row in mission_rows:
            mission_id, mission_name = mission_row
            mission_dict = {
                "mission_id": mission_id,
                "mission_name": mission_name,
                "kpis": []
            }
            # ดึง kpis สำหรับ mission นี้
            cur.execute("SELECT id, kpi_name, kpi_category FROM kpis WHERE mission_id = %s", (mission_id,))
            kpi_rows = cur.fetchall()
            for kpi_row in kpi_rows:
                kpi_id, kpi_name, kpi_category = kpi_row
                kpi_dict = {
                    "kpi_id": kpi_id,
                    "kpi_name": kpi_name,
                    "kpi_category": kpi_category,
                    "definitions": []
                }
                # ดึง definitions ที่เชื่อมโยงกับ KPI นี้
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
        employees_list.append(employee_data)

    cur.close()
    conn.close()
    return jsonify(employees_list), 200

@api_bp.route('/employee/score', methods=['GET'])
def get_employees_by_score():
    score_param = request.args.get('score')
    if not score_param:
        return jsonify({"error": "score parameter is required"}), 400

    # ตรวจสอบว่า score_param มีรูปแบบเช่น "<4"
    if not score_param.startswith('<'):
        return jsonify({"error": "score parameter must start with '<'"}), 400

    try:
        threshold = float(score_param[1:])
    except ValueError:
        return jsonify({"error": "Invalid score threshold"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # ดึงข้อมูลพนักงานทั้งหมด
    cur.execute("SELECT emp_id, department FROM employees")
    employees_rows = cur.fetchall()

    employees_list = []
    for emp_row in employees_rows:
        emp_id, department = emp_row
        employee_data = {
            "emp_id": emp_id,
            "department": department,
            "missions": []
        }
        # ดึง missions สำหรับพนักงานนี้
        cur.execute("SELECT id, mission_name FROM missions WHERE emp_id = %s", (emp_id,))
        mission_rows = cur.fetchall()
        for mission_row in mission_rows:
            mission_id, mission_name = mission_row
            mission_dict = {
                "mission_id": mission_id,
                "mission_name": mission_name,
                "kpis": []
            }
            # ดึง kpis สำหรับ mission นี้
            cur.execute("SELECT id, kpi_name, kpi_category FROM kpis WHERE mission_id = %s", (mission_id,))
            kpi_rows = cur.fetchall()
            for kpi_row in kpi_rows:
                kpi_id, kpi_name, kpi_category = kpi_row
                kpi_dict = {
                    "kpi_id": kpi_id,
                    "kpi_name": kpi_name,
                    "kpi_category": kpi_category,
                    "definitions": []
                }
                # ดึง definitions สำหรับ KPI นี้ที่มี score น้อยกว่า threshold
                cur.execute("""
                    SELECT DISTINCT d.id, d.definition_text, d.weight, d.score
                    FROM definitions d
                    WHERE d.kpi_id = %s AND d.score < %s
                """, (kpi_id, threshold))
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
                # เพิ่ม KPI เฉพาะเมื่อมี definitions ที่ผ่านการกรอง
                if kpi_dict["definitions"]:
                    mission_dict["kpis"].append(kpi_dict)
            if mission_dict["kpis"]:
                employee_data["missions"].append(mission_dict)
        if employee_data["missions"]:
            employees_list.append(employee_data)

    cur.close()
    conn.close()
    return jsonify(employees_list), 200

@api_bp.route('/employee/', methods=['PUT'])
def update_employee_full_query():
    # รับ emp_id จาก query parameter
    emp_id = request.args.get('emp_id')
    if not emp_id:
        return jsonify({"error": "emp_id parameter is required"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # ตรวจสอบว่ามี employee นี้หรือไม่
    cur.execute("SELECT emp_id FROM employees WHERE emp_id = %s", (emp_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Employee not found"}), 404

    try:
        # 1. อัปเดตข้อมูลในตาราง employees (เช่น department)
        if "department" in data:
            new_department = data["department"]
            cur.execute("UPDATE employees SET department = %s WHERE emp_id = %s", (new_department, emp_id))

        # 2. อัปเดต missions (ถ้ามี)
        if "missions" in data and isinstance(data["missions"], list):
            for mission in data["missions"]:
                # หากมี mission_id ให้ update มิฉะนั้น insert ใหม่
                if "mission_id" in mission:
                    mission_id = mission["mission_id"]
                    if "mission_name" in mission:
                        cur.execute(
                            "UPDATE missions SET mission_name = %s WHERE id = %s AND emp_id = %s",
                            (mission["mission_name"], mission_id, emp_id)
                        )
                else:
                    cur.execute(
                        "INSERT INTO missions (emp_id, mission_name) VALUES (%s, %s) RETURNING id",
                        (emp_id, mission.get("mission_name", ""))
                    )
                    mission_id = cur.fetchone()[0]
                    mission["mission_id"] = mission_id

                # 3. อัปเดต kpis สำหรับ mission นี้ (ถ้ามี)
                if "kpis" in mission and isinstance(mission["kpis"], list):
                    for kpi in mission["kpis"]:
                        if "kpi_id" in kpi:
                            kpi_id = kpi["kpi_id"]
                            new_kpi_name = kpi.get("kpi_name", "")
                            new_kpi_category = kpi.get("kpi_category", "")
                            cur.execute(
                                "UPDATE kpis SET kpi_name = %s, kpi_category = %s WHERE id = %s",
                                (new_kpi_name, new_kpi_category, kpi_id)
                            )
                        else:
                            cur.execute(
                                "INSERT INTO kpis (mission_id, kpi_name, kpi_category) VALUES (%s, %s, %s) RETURNING id",
                                (mission["mission_id"], kpi.get("kpi_name", ""), kpi.get("kpi_category", ""))
                            )
                            kpi_id = cur.fetchone()[0]
                            kpi["kpi_id"] = kpi_id

                        # 4. อัปเดต definitions สำหรับ KPI นี้ (ถ้ามี)
                        if "definitions" in kpi and isinstance(kpi["definitions"], list):
                            for definition in kpi["definitions"]:
                                if "definition_id" in definition:
                                    definition_id = definition["definition_id"]
                                    new_text = definition.get("definition_text", "")
                                    new_weight = definition.get("weight", 0.0)
                                    new_score = definition.get("score", 0.0)
                                    cur.execute(
                                        "UPDATE definitions SET definition_text = %s, weight = %s, score = %s WHERE id = %s",
                                        (new_text, new_weight, new_score, definition_id)
                                    )
                                else:
                                    cur.execute(
                                        "INSERT INTO definitions (kpi_id, definition_text, weight, score) VALUES (%s, %s, %s, %s) RETURNING id",
                                        (kpi["kpi_id"], definition.get("definition_text", ""), definition.get("weight", 0.0), definition.get("score", 0.0))
                                    )
                                    def_id = cur.fetchone()[0]
                                    definition["definition_id"] = def_id

        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()
    return jsonify({
        "message": "Employee updated successfully",
        "emp_id": emp_id
    }), 200

@api_bp.route('/employee', methods=['POST'])
def create_employee():
    """
    สร้างข้อมูล employee ใหม่ พร้อมกับข้อมูลภารกิจ (missions), KPIs และ definitions
    ตัวอย่าง JSON payload:
    {
        "emp_id": "04959",
        "department": "Sales",
        "missions": [
            {
                "mission_name": "Mission A",
                "kpis": [
                    {
                        "kpi_name": "KPI 1",
                        "kpi_category": "Financial Performance",
                        "definitions": [
                            {
                                "definition_text": "Definition text 1",
                                "weight": 0.5,
                                "score": 3.2
                            },
                            {
                                "definition_text": "Definition text 2",
                                "weight": 0.5,
                                "score": 2.8
                            }
                        ]
                    }
                ]
            }
        ]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    emp_id = data.get("emp_id")
    department = data.get("department")
    if not emp_id or not department:
        return jsonify({"error": "emp_id and department are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # ตรวจสอบว่ามี employee ที่ emp_id นี้อยู่แล้วหรือไม่
        cur.execute("SELECT emp_id FROM employees WHERE emp_id = %s", (emp_id,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Employee already exists"}), 400

        # สร้าง employee ใหม่
        cur.execute(
            "INSERT INTO employees (emp_id, department) VALUES (%s, %s)",
            (emp_id, department)
        )

        # เพิ่ม missions (ถ้ามี)
        missions = data.get("missions", [])
        for mission in missions:
            mission_name = mission.get("mission_name", "")
            cur.execute(
                "INSERT INTO missions (emp_id, mission_name) VALUES (%s, %s) RETURNING id",
                (emp_id, mission_name)
            )
            mission_id = cur.fetchone()[0]

            # เพิ่ม KPIs สำหรับ mission นี้ (ถ้ามี)
            kpis = mission.get("kpis", [])
            for kpi in kpis:
                kpi_name = kpi.get("kpi_name", "")
                kpi_category = kpi.get("kpi_category", "")
                cur.execute(
                    "INSERT INTO kpis (mission_id, kpi_name, kpi_category) VALUES (%s, %s, %s) RETURNING id",
                    (mission_id, kpi_name, kpi_category)
                )
                kpi_id = cur.fetchone()[0]

                # เพิ่ม definitions สำหรับ KPI นี้ (ถ้ามี)
                definitions = kpi.get("definitions", [])
                for definition in definitions:
                    definition_text = definition.get("definition_text", "")
                    weight = definition.get("weight", 0.0)
                    score = definition.get("score", 0.0)
                    cur.execute(
                        "INSERT INTO definitions (kpi_id, definition_text, weight, score) VALUES (%s, %s, %s, %s)",
                        (kpi_id, definition_text, weight, score)
                    )

        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()
    return jsonify({"message": "Employee created successfully", "emp_id": emp_id}), 201

@api_bp.route('/employee/', methods=['DELETE'])
def delete_employee_by_query():
    # รับค่า emp_id จาก query parameter
    emp_id = request.args.get('emp_id')
    if not emp_id:
        return jsonify({"error": "emp_id parameter is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    # ตรวจสอบว่ามี employee ที่ emp_id นี้หรือไม่
    cur.execute("SELECT emp_id FROM employees WHERE emp_id = %s", (emp_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Employee not found"}), 404

    try:
        # ลบ definitions ที่เชื่อมโยงกับ kpis ที่อยู่ใน missions ของ employee นี้
        cur.execute("""
            DELETE FROM definitions
            WHERE kpi_id IN (
                SELECT id FROM kpis
                WHERE mission_id IN (
                    SELECT id FROM missions
                    WHERE emp_id = %s
                )
            )
        """, (emp_id,))
        
        # ลบ kpis ที่อยู่ใน missions ของ employee นี้
        cur.execute("""
            DELETE FROM kpis
            WHERE mission_id IN (
                SELECT id FROM missions
                WHERE emp_id = %s
            )
        """, (emp_id,))
        
        # ลบ missions ของ employee นี้
        cur.execute("DELETE FROM missions WHERE emp_id = %s", (emp_id,))
        
        # ลบ employee
        cur.execute("DELETE FROM employees WHERE emp_id = %s", (emp_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"error": str(e)}), 500

    cur.close()
    conn.close()
    return jsonify({"message": f"Employee {emp_id} and all associated records have been deleted."}), 200