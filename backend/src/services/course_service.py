# from src.db import get_conn
# from psycopg.rows import dict_row


# class CourseService:

#     def get_all_courses(self):
#         sql = """
#             SELECT id, course_name, course_code, description
#             FROM course
#             ORDER BY course_name;
#         """
#         with get_conn() as conn:
#             with conn.cursor(row_factory=dict_row) as cur:
#                 cur.execute(sql)
#                 courses = cur.fetchall()
#         return courses


from src.db import get_conn
from psycopg.rows import dict_row
from typing import Optional, List, Dict, Any


class CourseService:

    def get_all_courses(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all courses with student count and instructor information.
        Optional filter by status (active/inactive).
        """
        sql = """
            SELECT 
                c.id,
                c.course_name,
                c.course_code,
                c.description,
                c.status,
                COUNT(DISTINCT sc.student_id) as number_student,
                COALESCE(
                    STRING_AGG(DISTINCT u.user_email, ', '),
                    'No instructor assigned'
                ) as instructor
            FROM public.course c
            LEFT JOIN public."studentCourse" sc ON c.id = sc.course_id
            LEFT JOIN public."intrcutorCourse" ic ON c.id = ic.course_id
            LEFT JOIN public."user" u ON ic.intructor_id = u.id AND u.user_role = 'teacher'
        """
        
        params = []
        if status:
            sql += " WHERE c.status = %s"
            params.append(status)
        
        sql += """
            GROUP BY c.id, c.course_name, c.course_code, c.description, c.status
            ORDER BY c.course_name;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                courses = cur.fetchall()
        
        return courses

    def get_course_by_id(self, course_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific course"""
        sql = """
            SELECT 
                c.id,
                c.course_name,
                c.course_code,
                c.description,
                c.status,
                COUNT(DISTINCT sc.student_id) as number_student
            FROM public.course c
            LEFT JOIN public."studentCourse" sc ON c.id = sc.course_id
            WHERE c.id = %s
            GROUP BY c.id, c.course_name, c.course_code, c.description, c.status;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (course_id,))
                course = cur.fetchone()
        
        return course

    def create_course(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new course"""
        # Check if course code already exists
        check_sql = "SELECT id FROM public.course WHERE course_code = %s;"
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(check_sql, (course_data['course_code'],))
                existing = cur.fetchone()
                
                if existing:
                    raise ValueError(f"Course code '{course_data['course_code']}' already exists")
                
                # Insert new course
                insert_sql = """
                    INSERT INTO public.course (course_name, course_code, description, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, course_name, course_code, description, status;
                """
                
                cur.execute(insert_sql, (
                    course_data['course_name'],
                    course_data['course_code'],
                    course_data.get('description'),
                    course_data.get('status', 'active')
                ))
                
                new_course = cur.fetchone()
                conn.commit()
        
        return new_course

    def update_course(self, course_id: int, course_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing course"""
        # Build dynamic update query
        update_fields = []
        params = []
        
        for field in ['course_name', 'course_code', 'description', 'status']:
            if field in course_data and course_data[field] is not None:
                update_fields.append(f"{field} = %s")
                params.append(course_data[field])
        
        if not update_fields:
            return self.get_course_by_id(course_id)
        
        params.append(course_id)
        
        sql = f"""
            UPDATE public.course
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, course_name, course_code, description, status;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Check if course code is being changed and if it conflicts
                if 'course_code' in course_data:
                    check_sql = "SELECT id FROM public.course WHERE course_code = %s AND id != %s;"
                    cur.execute(check_sql, (course_data['course_code'], course_id))
                    existing = cur.fetchone()
                    if existing:
                        raise ValueError(f"Course code '{course_data['course_code']}' already exists")
                
                cur.execute(sql, params)
                updated_course = cur.fetchone()
                
                if updated_course:
                    conn.commit()
        
        return updated_course

    def update_course_status(self, course_id: int, status: str) -> Optional[Dict[str, Any]]:
        """Update only the status of a course (activate/deactivate)"""
        sql = """
            UPDATE public.course
            SET status = %s
            WHERE id = %s
            RETURNING id, course_name, course_code, description, status;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (status, course_id))
                updated_course = cur.fetchone()
                
                if updated_course:
                    conn.commit()
        
        return updated_course

    def delete_course(self, course_id: int) -> bool:
        """Delete a course (only if status is inactive)"""
        # Check if course exists and is inactive
        check_sql = "SELECT status FROM public.course WHERE id = %s;"
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(check_sql, (course_id,))
                course = cur.fetchone()
                
                if not course:
                    return False
                
                if course['status'] != 'inactive':
                    raise ValueError("Only inactive courses can be deleted. Please deactivate the course first.")
                
                # Delete related records first (to maintain referential integrity)
                # Delete student enrollments
                cur.execute('DELETE FROM public."studentCourse" WHERE course_id = %s;', (course_id,))
                
                # Delete instructor assignments
                cur.execute('DELETE FROM public."intrcutorCourse" WHERE course_id = %s;', (course_id,))
                
                # Delete exams and related data
                cur.execute("""
                    DELETE FROM public."submissionAnswer" 
                    WHERE question_id IN (
                        SELECT id FROM public.question WHERE exam_id IN (
                            SELECT id FROM public.exams WHERE course = %s
                        )
                    );
                """, (course_id,))
                
                cur.execute("""
                    DELETE FROM public.submission 
                    WHERE exam_code IN (SELECT id FROM public.exams WHERE course = %s);
                """, (course_id,))
                
                cur.execute("""
                    DELETE FROM public."questionOption" 
                    WHERE question_id IN (
                        SELECT id FROM public.question WHERE exam_id IN (
                            SELECT id FROM public.exams WHERE course = %s
                        )
                    );
                """, (course_id,))
                
                cur.execute("""
                    DELETE FROM public.question 
                    WHERE exam_id IN (SELECT id FROM public.exams WHERE course = %s);
                """, (course_id,))
                
                cur.execute("DELETE FROM public.exams WHERE course = %s;", (course_id,))
                
                # Finally delete the course
                cur.execute("DELETE FROM public.course WHERE id = %s;", (course_id,))
                
                conn.commit()
        
        return True

    def get_course_students(self, course_id: int) -> List[Dict[str, Any]]:
        """Get all students enrolled in a course"""
        sql = """
            SELECT 
                u.id,
                u.user_email,
                u.student_id,
                sc.id as enrollment_id
            FROM public."studentCourse" sc
            JOIN public."user" u ON sc.student_id = u.id
            WHERE sc.course_id = %s AND u.user_role = 'student'
            ORDER BY u.user_email;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (course_id,))
                students = cur.fetchall()
        
        return students

    def get_course_exams(self, course_id: int) -> List[Dict[str, Any]]:
        """Get all exams for a course"""
        sql = """
            SELECT 
                id,
                title,
                exam_code,
                date,
                start_time,
                end_time,
                duration,
                status,
                created_at
            FROM public.exams
            WHERE course = %s
            ORDER BY date DESC, start_time DESC;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (course_id,))
                exams = cur.fetchall()
        
        return exams

    def get_course_instructors(self, course_id: int) -> List[Dict[str, Any]]:
        """Get instructor(s) assigned to a course"""
        sql = """
            SELECT 
                u.id,
                u.user_email,
                ic.id as assignment_id
            FROM public."intrcutorCourse" ic
            JOIN public."user" u ON ic.intructor_id = u.id
            WHERE ic.course_id = %s AND u.user_role = 'teacher'
            ORDER BY u.user_email;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (course_id,))
                instructors = cur.fetchall()
        
        return instructors

    def assign_instructor(self, course_id: int, instructor_id: int) -> Dict[str, Any]:
        """Assign an instructor to a course"""
        # Check if instructor exists and is an instructor
        check_instructor_sql = """
            SELECT id, user_email FROM public."user" 
            WHERE id = %s AND user_role = 'teacher';
        """
        
        # Check if assignment already exists
        check_assignment_sql = """
            SELECT id FROM public."intrcutorCourse" 
            WHERE course_id = %s AND intructor_id = %s;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify instructor exists
                cur.execute(check_instructor_sql, (instructor_id,))
                instructor = cur.fetchone()
                
                if not instructor:
                    raise ValueError("Instructor not found or user is not an instructor")
                
                # Check if already assigned
                cur.execute(check_assignment_sql, (course_id, instructor_id))
                existing = cur.fetchone()
                
                if existing:
                    raise ValueError("This instructor is already assigned to this course")
                
                # Create assignment
                insert_sql = """
                    INSERT INTO public."intrcutorCourse" (course_id, intructor_id)
                    VALUES (%s, %s)
                    RETURNING id, course_id, intructor_id;
                """
                
                cur.execute(insert_sql, (course_id, instructor_id))
                assignment = cur.fetchone()
                conn.commit()
        
        return {
            'id': assignment['id'],
            'course_id': assignment['course_id'],
            'instructor_id': assignment['intructor_id'],
            'instructor_email': instructor['user_email']
        }

    def remove_instructor(self, course_id: int, instructor_id: int) -> bool:
        """Remove an instructor from a course"""
        sql = """
            DELETE FROM public."intrcutorCourse"
            WHERE course_id = %s AND intructor_id = %s
            RETURNING id;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (course_id, instructor_id))
                deleted = cur.fetchone()
                
                if deleted:
                    conn.commit()
                    return True
        
        return False

    def get_all_instructors(self) -> List[Dict[str, Any]]:
        """Get all available instructors"""
        sql = """
            SELECT 
                id,
                user_email,
                student_id
            FROM public."user"
            WHERE user_role = 'teacher'
            ORDER BY user_email;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql)
                instructors = cur.fetchall()
        
        return instructors
    
 ################################ NEW METHODS FOR STUDENT ENROLLMENT ################################
    def get_student_courses(self, student_id: int) -> List[Dict[str, Any]]:
        """Get all courses a student is enrolled in"""
        sql = """
            SELECT 
                c.id,
                c.course_name,
                c.course_code,
                c.description,
                c.status,
                COUNT(DISTINCT sc2.student_id) as number_student,
                COALESCE(
                    STRING_AGG(DISTINCT u.user_email, ', '),
                    'No instructor assigned'
                ) as instructor,
                sc.id as enrollment_id
            FROM public."studentCourse" sc
            JOIN public.course c ON sc.course_id = c.id
            LEFT JOIN public."studentCourse" sc2 ON c.id = sc2.course_id
            LEFT JOIN public."intrcutorCourse" ic ON c.id = ic.course_id
            LEFT JOIN public."user" u ON ic.intructor_id = u.id AND u.user_role = 'teacher'
            WHERE sc.student_id = %s AND c.status = 'active'
            GROUP BY c.id, c.course_name, c.course_code, c.description, c.status, sc.id
            ORDER BY c.course_name;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (student_id,))
                courses = cur.fetchall()
        
        return courses

    def get_available_courses_for_student(self, student_id: int) -> List[Dict[str, Any]]:
        """Get all courses a student can enroll in (not already enrolled and active)"""
        sql = """
            SELECT 
                c.id,
                c.course_name,
                c.course_code,
                c.description,
                c.status,
                COUNT(DISTINCT sc.student_id) as number_student,
                COALESCE(
                    STRING_AGG(DISTINCT u.user_email, ', '),
                    'No instructor assigned'
                ) as instructor
            FROM public.course c
            LEFT JOIN public."studentCourse" sc ON c.id = sc.course_id
            LEFT JOIN public."intrcutorCourse" ic ON c.id = ic.course_id
            LEFT JOIN public."user" u ON ic.intructor_id = u.id AND u.user_role = 'teacher'
            WHERE c.status = 'active'
            AND c.id NOT IN (
                SELECT course_id 
                FROM public."studentCourse" 
                WHERE student_id = %s
            )
            GROUP BY c.id, c.course_name, c.course_code, c.description, c.status
            ORDER BY c.course_name;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (student_id,))
                courses = cur.fetchall()
        
        return courses

    def enroll_student(self, student_id: int, course_id: int) -> Dict[str, Any]:
        """Enroll a student in a course"""
        # Check if student exists
        check_student_sql = """
            SELECT id, user_email FROM public."user" 
            WHERE id = %s AND user_role = 'student';
        """
        
        # Check if course exists and is active
        check_course_sql = """
            SELECT id, course_name, status FROM public.course 
            WHERE id = %s;
        """
        
        # Check if already enrolled
        check_enrollment_sql = """
            SELECT id FROM public."studentCourse" 
            WHERE student_id = %s AND course_id = %s;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Verify student exists
                cur.execute(check_student_sql, (student_id,))
                student = cur.fetchone()
                
                if not student:
                    raise ValueError("Student not found or user is not a student")
                
                # Verify course exists and is active
                cur.execute(check_course_sql, (course_id,))
                course = cur.fetchone()
                
                if not course:
                    raise ValueError("Course not found")
                
                if course['status'] != 'active':
                    raise ValueError("Cannot enroll in an inactive course")
                
                # Check if already enrolled
                cur.execute(check_enrollment_sql, (student_id, course_id))
                existing = cur.fetchone()
                
                if existing:
                    raise ValueError("Student is already enrolled in this course")
                
                # Create enrollment
                insert_sql = """
                    INSERT INTO public."studentCourse" (student_id, course_id)
                    VALUES (%s, %s)
                    RETURNING id, student_id, course_id;
                """
                
                cur.execute(insert_sql, (student_id, course_id))
                enrollment = cur.fetchone()
                conn.commit()
        
        return {
            'id': enrollment['id'],
            'student_id': enrollment['student_id'],
            'course_id': enrollment['course_id'],
            'course_name': course['course_name'],
            'student_email': student['user_email']
        }

    def unenroll_student(self, student_id: int, course_id: int) -> bool:
        """Unenroll a student from a course"""
        sql = """
            DELETE FROM public."studentCourse"
            WHERE student_id = %s AND course_id = %s
            RETURNING id;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (student_id, course_id))
                deleted = cur.fetchone()
                
                if deleted:
                    conn.commit()
                    return True
        
        return False

    def is_student_enrolled(self, student_id: int, course_id: int) -> bool:
        """Check if a student is enrolled in a specific course"""
        sql = """
            SELECT id FROM public."studentCourse"
            WHERE student_id = %s AND course_id = %s;
        """
        
        with get_conn() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(sql, (student_id, course_id))
                result = cur.fetchone()
        
        return result is not None