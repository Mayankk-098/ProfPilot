export type Lecturer = {
  id: string;
  name: string;
  initials: string;
  title: string;
  department: string;
  email: string;
  experience: number;
  researchInterests: string[];
  teachingInterests: string[];
  posts: number;
  resources: number;
  connections: number;
};

export type SyllabusTopic = {
  id: string;
  name: string;
  completed: boolean;
  plannedDate?: string;
};

export type SyllabusUnit = {
  id: string;
  name: string;
  progress: number;
  topics: SyllabusTopic[];
};

export type Course = {
  id: string;
  code: string;
  name: string;
  shortName: string;
  section: string;
  department: string;

  progress: number;
  plannedProgress: number;

  status: "on_schedule" | "behind" | "ahead";

  currentPace: number;
  requiredPace: number;

  predictedCompletion: string;
  plannedCompletion: string;

  totalStudents: number;
  presentToday: number;
  absentToday: number;

  syllabus: SyllabusUnit[];
};

export type ScheduleItem = {
  id: string;
  courseId?: string;
  subject: string;
  code?: string;
  batch: string;
  time: string;
  period: "AM" | "PM";
  room: string;
  type: "class" | "meeting";
};

export type AttendanceStudent = {
  entryNumber: string;
  attendance: number;
  classesAttended: number;
  classesConducted: number;
};

export type LectureLog = {
  id: string;
  courseId: string;
  date: string;
  duration: number;
  description: string;
  topics: string[];
};

export type CommunityPost = {
  id: string;
  authorId: string;
  text: string;
  likes: number;
  comments: number;
  createdAt: string;
};

export const currentLecturer: Lecturer = {
  id: "lecturer_001",
  name: "Dr. Sharma",
  initials: "DS",
  title: "Assistant Professor",
  department: "Computer Science & Engineering",
  email: "sharma@university.edu",
  experience: 8,
  researchInterests: [
    "Machine Learning",
    "Computer Vision",
    "Artificial Intelligence",
    "Data Science",
  ],
  teachingInterests: [
    "Artificial Intelligence",
    "Database Systems",
    "Machine Learning",
  ],
  posts: 17,
  resources: 24,
  connections: 42,
};

export const lecturers: Lecturer[] = [
  currentLecturer,

  {
    id: "lecturer_002",
    name: "Dr. Mehta",
    initials: "DM",
    title: "Associate Professor",
    department: "Computer Science & Engineering",
    email: "mehta@university.edu",
    experience: 11,
    researchInterests: [
      "Database Systems",
      "Distributed Systems",
      "Cloud Computing",
    ],
    teachingInterests: [
      "DBMS",
      "Operating Systems",
      "Distributed Systems",
    ],
    posts: 24,
    resources: 31,
    connections: 67,
  },

  {
    id: "lecturer_003",
    name: "Dr. Rao",
    initials: "DR",
    title: "Assistant Professor",
    department: "Information Technology",
    email: "rao@university.edu",
    experience: 6,
    researchInterests: [
      "Deep Learning",
      "Natural Language Processing",
      "Data Mining",
    ],
    teachingInterests: [
      "Machine Learning",
      "Artificial Intelligence",
      "NLP",
    ],
    posts: 19,
    resources: 28,
    connections: 51,
  },

  {
    id: "lecturer_004",
    name: "Dr. Kapoor",
    initials: "DK",
    title: "Professor",
    department: "Computer Science & Engineering",
    email: "kapoor@university.edu",
    experience: 15,
    researchInterests: [
      "Computer Networks",
      "Cybersecurity",
      "Distributed Systems",
    ],
    teachingInterests: [
      "Computer Networks",
      "Network Security",
      "Operating Systems",
    ],
    posts: 37,
    resources: 46,
    connections: 93,
  },
];

export const courses: Course[] = [
  {
    id: "dbms",
    code: "CSE-302",
    name: "Database Management Systems",
    shortName: "DBMS",
    section: "CSE-B",
    department: "Computer Science & Engineering",

    progress: 68,
    plannedProgress: 74,

    status: "behind",

    currentPace: 0.62,
    requiredPace: 0.71,

    predictedCompletion: "7 December 2026",
    plannedCompletion: "3 December 2026",

    totalStudents: 62,
    presentToday: 56,
    absentToday: 6,

    syllabus: [
      {
        id: "dbms-u1",
        name: "Unit 1 — Database Fundamentals",
        progress: 100,
        topics: [
          {
            id: "dbms-t1",
            name: "ER Model",
            completed: true,
            plannedDate: "18 September 2026",
          },
          {
            id: "dbms-t2",
            name: "Relational Model",
            completed: true,
            plannedDate: "20 September 2026",
          },
          {
            id: "dbms-t3",
            name: "SQL",
            completed: true,
            plannedDate: "22 September 2026",
          },
        ],
      },

      {
        id: "dbms-u2",
        name: "Unit 2 — Database Design",
        progress: 72,
        topics: [
          {
            id: "dbms-t4",
            name: "Functional Dependencies",
            completed: true,
            plannedDate: "24 September 2026",
          },
          {
            id: "dbms-t5",
            name: "Normalization",
            completed: true,
            plannedDate: "26 September 2026",
          },
          {
            id: "dbms-t6",
            name: "First Normal Form",
            completed: true,
          },
          {
            id: "dbms-t7",
            name: "Second Normal Form",
            completed: true,
          },
          {
            id: "dbms-t8",
            name: "Third Normal Form",
            completed: true,
          },
          {
            id: "dbms-t9",
            name: "BCNF",
            completed: false,
            plannedDate: "28 September 2026",
          },
        ],
      },

      {
        id: "dbms-u3",
        name: "Unit 3 — Indexing & Storage",
        progress: 0,
        topics: [
          {
            id: "dbms-t10",
            name: "Indexing",
            completed: false,
          },
          {
            id: "dbms-t11",
            name: "B Trees",
            completed: false,
          },
          {
            id: "dbms-t12",
            name: "B+ Trees",
            completed: false,
          },
        ],
      },
    ],
  },

  {
    id: "ai",
    code: "CSE-304",
    name: "Artificial Intelligence",
    shortName: "AI",
    section: "CSE-A",
    department: "Computer Science & Engineering",

    progress: 73,
    plannedProgress: 71,

    status: "ahead",

    currentPace: 0.74,
    requiredPace: 0.68,

    predictedCompletion: "1 December 2026",
    plannedCompletion: "4 December 2026",

    totalStudents: 58,
    presentToday: 53,
    absentToday: 5,

    syllabus: [
      {
        id: "ai-u1",
        name: "Unit 1 — Introduction to AI",
        progress: 100,
        topics: [
          {
            id: "ai-t1",
            name: "Introduction to Artificial Intelligence",
            completed: true,
          },
          {
            id: "ai-t2",
            name: "Intelligent Agents",
            completed: true,
          },
          {
            id: "ai-t3",
            name: "Problem Solving",
            completed: true,
          },
        ],
      },

      {
        id: "ai-u2",
        name: "Unit 2 — Machine Learning",
        progress: 65,
        topics: [
          {
            id: "ai-t4",
            name: "Supervised Learning",
            completed: true,
          },
          {
            id: "ai-t5",
            name: "Regression",
            completed: true,
          },
          {
            id: "ai-t6",
            name: "Classification",
            completed: true,
          },
          {
            id: "ai-t7",
            name: "Decision Trees",
            completed: false,
          },
        ],
      },
    ],
  },
];

export const timetable: ScheduleItem[] = [
  {
    id: "class_001",
    courseId: "dbms",
    subject: "Database Management Systems",
    code: "CSE-302",
    batch: "CSE-B",
    time: "10:00",
    period: "AM",
    room: "Block C · Room 204",
    type: "class",
  },

  {
    id: "class_002",
    courseId: "ai",
    subject: "Artificial Intelligence",
    code: "CSE-304",
    batch: "CSE-A",
    time: "12:00",
    period: "PM",
    room: "Block B · Room 108",
    type: "class",
  },

  {
    id: "meeting_001",
    subject: "Faculty Meeting",
    batch: "Faculty",
    time: "03:00",
    period: "PM",
    room: "Admin Block",
    type: "meeting",
  },
];

export const attendanceStudents: AttendanceStudent[] = [
  {
    entryNumber: "24BCS018",
    attendance: 71,
    classesAttended: 27,
    classesConducted: 38,
  },
  {
    entryNumber: "24BCS031",
    attendance: 68,
    classesAttended: 26,
    classesConducted: 38,
  },
  {
    entryNumber: "24BCS047",
    attendance: 73,
    classesAttended: 28,
    classesConducted: 38,
  },
  {
    entryNumber: "24BCS052",
    attendance: 89,
    classesAttended: 34,
    classesConducted: 38,
  },
];

export const lectureLogs: LectureLog[] = [
  {
    id: "lecture_001",
    courseId: "dbms",
    date: "18 September 2026",
    duration: 52,
    description: "Covered ER model and ER diagram notation.",
    topics: ["ER Model"],
  },

  {
    id: "lecture_002",
    courseId: "dbms",
    date: "20 September 2026",
    duration: 55,
    description: "Introduced the relational model and relational schemas.",
    topics: ["Relational Model"],
  },

  {
    id: "lecture_003",
    courseId: "dbms",
    date: "22 September 2026",
    duration: 50,
    description: "Covered SQL fundamentals and basic queries.",
    topics: ["SQL"],
  },

  {
    id: "lecture_004",
    courseId: "dbms",
    date: "24 September 2026",
    duration: 54,
    description: "Covered functional dependencies with examples.",
    topics: ["Functional Dependencies"],
  },

  {
    id: "lecture_005",
    courseId: "dbms",
    date: "26 September 2026",
    duration: 51,
    description:
      "Covered normalization, 2NF and 3NF with worked examples.",
    topics: ["Normalization", "2NF", "3NF"],
  },
];

export const communityPosts: CommunityPost[] = [
  {
    id: "post_001",
    authorId: "lecturer_002",
    text: "Does anyone have good material for teaching B+ Trees?",
    likes: 8,
    comments: 4,
    createdAt: "2 hours ago",
  },

  {
    id: "post_002",
    authorId: "lecturer_003",
    text: "Sharing my latest DBMS assignment with the faculty.",
    likes: 13,
    comments: 6,
    createdAt: "5 hours ago",
  },

  {
    id: "post_003",
    authorId: "lecturer_004",
    text:
      "Has anyone tried a better way of tracking syllabus progress?",
    likes: 21,
    comments: 9,
    createdAt: "Yesterday",
  },
];

export function getCourseById(id: string) {
  return courses.find((course) => course.id === id);
}

export function getLecturerById(id: string) {
  return lecturers.find((lecturer) => lecturer.id === id);
}

export function getLecturesForCourse(courseId: string) {
  return lectureLogs.filter(
    (lecture) => lecture.courseId === courseId
  );
}