// TEMPORARY COMMUNITY UI DATA.
//
// The current backend does not expose dedicated
// community/faculty/search/resource endpoints.
//
// This data exists only to keep the mobile UI usable
// until those backend endpoints are available.
//
// Replace these sources with real API data later.
// Do not create a second backend inside mobile.

export const TEMP_FACULTY = [
  {
    id: "temp-faculty-1",
    name: "Dr. Mehta",
    department: "Computer Science",

    teachingInterests: [
      "Database Systems",
      "Algorithms",
      "Data Structures",
    ],

    researchInterests: [
      "Artificial Intelligence",
      "Information Retrieval",
    ],
  },

  {
    id: "temp-faculty-2",
    name: "Dr. Rao",
    department:
      "Information Technology",

    teachingInterests: [
      "Computer Networks",
      "Cyber Security",
    ],

    researchInterests: [
      "Computer Vision",
      "Machine Learning",
    ],
  },

  {
    id: "temp-faculty-3",
    name: "Dr. Kapoor",
    department: "Computer Science",

    teachingInterests: [
      "Operating Systems",
      "Distributed Systems",
    ],

    researchInterests: [
      "Cloud Computing",
      "Distributed Computing",
    ],
  },
];

export const TEMP_POSTS = [
  {
    id: "temp-post-1",
    author: "Dr. Mehta",
    department: "Computer Science",
    text:
      "Does anyone have good material for teaching B+ Trees?",
    likes: 8,
    comments: 4,
  },

  {
    id: "temp-post-2",
    author: "Dr. Rao",
    department:
      "Information Technology",
    text:
      "Sharing my latest DBMS assignment with faculty.",
    likes: 13,
    comments: 6,
  },

  {
    id: "temp-post-3",
    author: "Dr. Kapoor",
    department: "Computer Science",
    text:
      "Has anyone tried a better way of tracking syllabus progress?",
    likes: 21,
    comments: 9,
  },
];

export const TEMP_RESOURCES = [
  {
    id: "temp-resource-1",
    title: "DBMS Teaching Resources",
    description:
      "Faculty-shared resources for database teaching.",
    sharedBy: "Dr. Rao",
  },

  {
    id: "temp-resource-2",
    title:
      "Algorithms Reference Material",
    description:
      "Useful material for algorithm lectures.",
    sharedBy: "Dr. Mehta",
  },

  {
    id: "temp-resource-3",
    title:
      "Computer Vision Starter Material",
    description:
      "Introductory teaching resources for computer vision.",
    sharedBy: "Dr. Kapoor",
  },
];