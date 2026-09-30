import { API_BASE_URL } from "../config/api";

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

export type CourseDetail = CourseSummary & {
  department: string;
  syllabus: SyllabusUnit[];
  lectures: Lecture[];
};

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


// -----------------------------
// Generic request helper
// -----------------------------

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `ProfPilot API error: ${response.status}`
    );
  }

  return response.json();
}


// -----------------------------
// Courses
// -----------------------------

export async function getCourses(): Promise<CourseSummary[]> {
  return request<CourseSummary[]>("/courses/");
}


export async function getCourse(
  courseId: string
): Promise<CourseDetail> {
  return request<CourseDetail>(
    `/courses/${courseId}`
  );
}


// -----------------------------
// AI
// -----------------------------

export async function queryProfPilotAI(
  requestData: AIQueryRequest
): Promise<AIQueryResponse> {
  return request<AIQueryResponse>(
    "/ai/query",
    {
      method: "POST",

      body: JSON.stringify(requestData),
    }
  );
}
export type ScheduleItem = {
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
export async function getSchedule(): Promise<ScheduleItem[]> {
  return request<ScheduleItem[]>("/schedule/");
}