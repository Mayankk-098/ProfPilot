import { API_BASE_URL } from "../config/api";

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function clearAccessToken() {
  accessToken = null;
}

// ================================
// AUTH
// ================================

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterRequest = {
  name: string;
  email: string;
  password: string;
  department: string;
  title: string;
};

export type CurrentUser = {
  id: number;
  email: string;
  lecturer_id: string;
  name: string;
  title: string;
  department: string;
};

// ================================
// COURSES
// ================================

export type CourseSummary = {
  id: string;
  code: string;
  name: string;
  short_name: string;
  section: string;

  progress: number;
  planned_progress: number;

  current_pace: number;
  required_pace: number;

  predicted_completion: string;
  planned_completion: string;

  total_students: number;
  present_today: number;
  absent_today: number;
};

export type SyllabusTopic = {
  id: string;
  name: string;
  completed: boolean;
  planned_date: string | null;
};

export type SyllabusUnit = {
  id: string;
  name: string;
  progress: number;
  topics: SyllabusTopic[];
};

export type Lecture = {
  id: string;
  date: string;
  duration: number;
  description: string;
};

export type CourseDetail =
  CourseSummary & {
    department: string;
    syllabus: SyllabusUnit[];
    lectures: Lecture[];
  };

// ================================
// SCHEDULE
// ================================

export type ScheduleItem = {
  id: string;
  subject: string;
  code: string | null;
  batch: string;
  weekday: number;

  start_time: string | null;
  end_time: string | null;

  room: string | null;
  item_type: string;

  lecturer_id: string | null;
  course_id: string | null;

  status: string;
  date: string;
  original_date: string | null;

  time: string | null;
  period: string | null;
};

// ================================
// CONTEXT
// ================================

export type ContextLecturer = {
  id: string;
  name: string;
  title: string;
  department: string;
};

export type ContextScheduleItem = {
  id: string;
  subject: string;
  code: string | null;
  batch: string;
  time: string;
  period: string;
  room: string;
  item_type: string;
  course_id: string | null;
};

export type AcademicContext = {
  current_date: string;

  lecturer: ContextLecturer;

  selected_course:
    CourseSummary | null;

  next_class:
    ContextScheduleItem | null;

  today_schedule:
    ContextScheduleItem[];

  courses: CourseSummary[];

  recent_lectures: Lecture[];

  alerts: string[];

  summary: Record<string, any>;
};

// ================================
// ATTENDANCE
// ================================

export type AttendanceStudent = {
  student_id: string;
  roll_no: string;
  name: string;

  attended: number;
  total: number;

  percentage: number | null;

  flagged: boolean;

  classes_needed_to_recover: number;
};

export type AttendanceStatus =
  | "present"
  | "absent"
  | "excused";

export type AttendanceSessionRecord = {
  student_id: string;
  status: AttendanceStatus;
};

export type AttendanceSessionResponse = {
  course_id: string;
  class_date: string;
  recorded: boolean;
  records: AttendanceSessionRecord[];
};

export type AttendanceCourseResponse = {
  course_id: string;
  course_code: string;
  short_name: string;
  section: string;

  threshold_pct: number;

  classes_held: number;

  last_class_date: string | null;

  total_students: number;

  class_average_pct:
    number | null;

  present_last_class: number;
  absent_last_class: number;

  flagged_count: number;

  students: AttendanceStudent[];
};

// ================================
// AI
// ================================

export type AIQueryRequest = {
  message: string;
  course_id?: string;
};

export type AIQueryResponse = {
  type: string;
  answer: string;

  data?: Record<string, any>;

  confidence?: number;

  requires_confirmation?: boolean;
};

export type AIExecuteRequest = {
  confirmed: boolean;
  action_plan: Record<string, any>;
};

// ================================
// REQUEST HELPER
// ================================

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,

      headers: {
        Accept: "application/json",

        "Content-Type":
          "application/json",

        ...(accessToken
          ? {
              Authorization:
                `Bearer ${accessToken}`,
            }
          : {}),

        ...(options.headers || {}),
      },
    }
  );

  const contentType =
    response.headers.get(
      "content-type"
    ) || "";

  const data =
    contentType.includes(
      "application/json"
    )
      ? await response.json()
      : null;

  if (response.status === 401) {
    clearAccessToken();
  }

  if (!response.ok) {
    
    const rawMessage =
      data?.detail ||
      data?.message ||
      `API error: ${response.status}`;

    const message =
      typeof rawMessage === "string"
        ? rawMessage
        : JSON.stringify(rawMessage);

    throw new Error(message);
  }

  return data as T;
}

// ================================
// AUTH APIs
// ================================

export async function registerLecturer(
  data: RegisterRequest
): Promise<LoginResponse> {
  const result =
    await request<LoginResponse>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );

  setAccessToken(
    result.access_token
  );

  return result;
}

export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
  const result =
    await request<LoginResponse>(
      "/auth/login",
      {
        method: "POST",

        body: JSON.stringify({
          email,
          password,
        }),
      }
    );

  setAccessToken(
    result.access_token
  );

  return result;
}

export async function getMe(): Promise<CurrentUser> {
  return request<CurrentUser>(
    "/auth/me"
  );
}

// ================================
// CONTEXT API
// ================================

export async function getAcademicContext(
  lecturerId: string,
  courseId?: string
): Promise<AcademicContext> {
  const query = courseId
    ? `?course_id=${encodeURIComponent(
        courseId
      )}`
    : "";

  return request<AcademicContext>(
    `/context/${encodeURIComponent(
      lecturerId
    )}${query}`
  );
}

// ================================
// COURSE APIs
// ================================

export async function getCourses(): Promise<
  CourseSummary[]
> {
  return request<CourseSummary[]>(
    "/courses/"
  );
}

export type CourseCreateRequest = {
  code: string;
  name: string;
  short_name: string;
  section: string;
  start_date: string;
  planned_end_date: string;
};

export async function createCourse(
  data: CourseCreateRequest
): Promise<CourseDetail> {
  return request<CourseDetail>(
    "/courses/",
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

export async function getCourse(
  courseId: string
): Promise<CourseDetail> {
  return request<CourseDetail>(
    `/courses/${encodeURIComponent(
      courseId
    )}`
  );
}

export type SyllabusUnitCreateRequest = {
  name: string;
};

export type SyllabusTopicCreateRequest = {
  name: string;
  planned_date?: string | null;
};

export async function createSyllabusUnit(
  courseId: string,
  data: SyllabusUnitCreateRequest
): Promise<SyllabusUnit> {
  return request<SyllabusUnit>(
    `/courses/${encodeURIComponent(courseId)}/units`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

export async function updateSyllabusUnit(
  courseId: string,
  unitId: string,
  name: string
): Promise<SyllabusUnit> {
  return request<SyllabusUnit>(
    `/courses/${encodeURIComponent(courseId)}/units/${encodeURIComponent(unitId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ name }),
    }
  );
}

export async function deleteSyllabusUnit(
  courseId: string,
  unitId: string
): Promise<void> {
  await request<void>(
    `/courses/${encodeURIComponent(courseId)}/units/${encodeURIComponent(unitId)}`,
    {
      method: "DELETE",
    }
  );
}

export async function reorderSyllabusUnits(
  courseId: string,
  ids: string[]
): Promise<SyllabusUnit[]> {
  return request<SyllabusUnit[]>(
    `/courses/${encodeURIComponent(courseId)}/units/reorder`,
    {
      method: "PUT",
      body: JSON.stringify({ ids }),
    }
  );
}

export async function createSyllabusTopic(
  courseId: string,
  unitId: string,
  data: SyllabusTopicCreateRequest
): Promise<SyllabusTopic> {
  return request<SyllabusTopic>(
    `/courses/${encodeURIComponent(courseId)}/units/${encodeURIComponent(unitId)}/topics`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

export async function updateSyllabusTopic(
  courseId: string,
  unitId: string,
  topicId: string,
  data: {
    name?: string;
    planned_date?: string | null;
    clear_planned_date?: boolean;
  }
): Promise<SyllabusTopic> {
  return request<SyllabusTopic>(
    `/courses/${encodeURIComponent(courseId)}/units/${encodeURIComponent(unitId)}/topics/${encodeURIComponent(topicId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

export async function deleteSyllabusTopic(
  courseId: string,
  unitId: string,
  topicId: string
): Promise<void> {
  await request<void>(
    `/courses/${encodeURIComponent(courseId)}/units/${encodeURIComponent(unitId)}/topics/${encodeURIComponent(topicId)}`,
    {
      method: "DELETE",
    }
  );
}

export async function reorderSyllabusTopics(
  courseId: string,
  unitId: string,
  ids: string[]
): Promise<SyllabusTopic[]> {
  return request<SyllabusTopic[]>(
    `/courses/${encodeURIComponent(courseId)}/units/${encodeURIComponent(unitId)}/topics/reorder`,
    {
      method: "PUT",
      body: JSON.stringify({ ids }),
    }
  );
}


// ================================
// SCHEDULE APIs
// ================================

export async function getSchedule(): Promise<
  ScheduleItem[]
> {
  return request<ScheduleItem[]>(
    "/schedule/"
  );
}

export async function getNextClass(): Promise<
  ScheduleItem | null
> {
  return request<ScheduleItem | null>(
    "/schedule/next"
  );
}

export type ScheduleTemplate = {
  id: string;
  subject: string;
  code: string | null;
  batch: string;
  weekday: number;
  start_time: string;
  end_time: string;
  room: string;
  item_type: string;
  lecturer_id: string;
  course_id: string | null;
};

export type ScheduleTemplateCreateRequest = {
  weekday: number;
  start_time: string;
  end_time: string;
  room: string;
  item_type?: "class" | "meeting";
  course_id?: string | null;
  subject?: string | null;
  code?: string | null;
  batch?: string | null;
};

export async function getScheduleTemplates(): Promise<ScheduleTemplate[]> {
  return request<ScheduleTemplate[]>("/schedule/templates");
}

export async function createScheduleTemplate(
  data: ScheduleTemplateCreateRequest
): Promise<ScheduleTemplate> {
  return request<ScheduleTemplate>("/schedule/templates", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateScheduleTemplate(
  itemId: string,
  data: Partial<ScheduleTemplateCreateRequest>
): Promise<ScheduleTemplate> {
  return request<ScheduleTemplate>(
    `/schedule/templates/${encodeURIComponent(itemId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

export async function deleteScheduleTemplate(
  itemId: string
): Promise<void> {
  await request<void>(
    `/schedule/templates/${encodeURIComponent(itemId)}`,
    {
      method: "DELETE",
    }
  );
}

// ================================
// STUDENT APIs
// ================================

export type Student = {
  id: string;
  roll_no: string;
  name: string;
  section: string;
  lecturer_id: string;
};

export type StudentCreateRequest = {
  roll_no: string;
  name: string;
  section?: string | null;
};

export type StudentUpdateRequest = {
  roll_no?: string;
  name?: string;
  section?: string;
};

export type StudentImportRowPreview = {
  line: number;
  roll_no: string;
  name: string;
  section: string;
  status: string;
  message: string;
};

export type StudentImportPreviewResponse = {
  course_id: string;
  valid_count: number;
  error_count: number;
  rows: StudentImportRowPreview[];
};

export type StudentImportResult = {
  created: number;
  enrolled: number;
};

export async function getCourseStudents(
  courseId: string
): Promise<Student[]> {
  return request<Student[]>(
    "/courses/" + encodeURIComponent(courseId) + "/students"
  );
}

export async function addCourseStudent(
  courseId: string,
  data: StudentCreateRequest
): Promise<Student> {
  return request<Student>(
    "/courses/" + encodeURIComponent(courseId) + "/students",
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

export async function updateStudent(
  studentId: string,
  data: StudentUpdateRequest
): Promise<Student> {
  return request<Student>(
    "/students/" + encodeURIComponent(studentId),
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

export async function removeCourseStudent(
  courseId: string,
  studentId: string
): Promise<void> {
  await request<void>(
    "/courses/" +
      encodeURIComponent(courseId) +
      "/students/" +
      encodeURIComponent(studentId),
    {
      method: "DELETE",
    }
  );
}

export async function previewStudentImport(
  courseId: string,
  content: string
): Promise<StudentImportPreviewResponse> {
  return request<StudentImportPreviewResponse>(
    "/courses/" +
      encodeURIComponent(courseId) +
      "/students/import/preview",
    {
      method: "POST",
      body: JSON.stringify({ content }),
    }
  );
}

export async function confirmStudentImport(
  courseId: string,
  students: {
    roll_no: string;
    name: string;
    section?: string;
  }[]
): Promise<StudentImportResult> {
  return request<StudentImportResult>(
    "/courses/" +
      encodeURIComponent(courseId) +
      "/students/import/confirm",
    {
      method: "POST",
      body: JSON.stringify({ students }),
    }
  );
}

// ================================
// ATTENDANCE API
// ================================

export async function getCourseAttendance(
  courseId: string
): Promise<AttendanceCourseResponse> {
  return request<AttendanceCourseResponse>(
    `/attendance/${encodeURIComponent(
      courseId
    )}`
  );
}

export async function getAttendanceSession(
  courseId: string,
  classDate: string
): Promise<AttendanceSessionResponse> {
  return request<AttendanceSessionResponse>(
    `/attendance/${encodeURIComponent(
      courseId
    )}/records/${encodeURIComponent(classDate)}`
  );
}

export async function submitAttendance(
  courseId: string,
  classDate: string,
  records: AttendanceSessionRecord[]
): Promise<{ course_id: string; class_date: string; created: number; updated: number }> {
  return request(
    `/attendance/${encodeURIComponent(
      courseId
    )}/records`,
    {
      method: "POST",
      body: JSON.stringify({
        class_date: classDate,
        records,
      }),
    }
  );
}

export async function correctAttendance(
  courseId: string,
  classDate: string,
  records: AttendanceSessionRecord[]
): Promise<{ course_id: string; class_date: string; created: number; updated: number }> {
  return request(
    `/attendance/${encodeURIComponent(
      courseId
    )}/records/${encodeURIComponent(classDate)}`,
    {
      method: "PUT",
      body: JSON.stringify({
        class_date: classDate,
        records,
      }),
    }
  );
}


// ================================
// AI APIs
// ================================

export async function queryProfPilotAI(
  requestData: AIQueryRequest
): Promise<AIQueryResponse> {
  return request<AIQueryResponse>(
    "/ai/query",
    {
      method: "POST",

      body: JSON.stringify(
        requestData
      ),
    }
  );
}

export async function executeAIAction(
  requestData: AIExecuteRequest
): Promise<AIQueryResponse> {
  return request<AIQueryResponse>(
    "/ai/execute",
    {
      method: "POST",

      body: JSON.stringify(
        requestData
      ),
    }
  );
}