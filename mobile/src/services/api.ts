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

export type CurrentUser = {
  id: string;
  email: string;
  lecturer_id: string;
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

export async function getCourse(
  courseId: string
): Promise<CourseDetail> {
  return request<CourseDetail>(
    `/courses/${encodeURIComponent(
      courseId
    )}`
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