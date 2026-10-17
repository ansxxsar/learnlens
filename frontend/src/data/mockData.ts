import type {
  Assignment,
  Course,
  ProgrammingLanguage,
  StudentProfile,
  StudentProgress,
} from "../types";

const programmingLanguages: ProgrammingLanguage[] = [
  "python",
  "java",
  "cpp",
  "javascript",
];

export const mockCourses: Course[] = [
  {
    id: 1,
    slug: "programming-foundations",
    title: "Programming Foundations",
    description:
      "Learn programming fundamentals through practical coding exercises.",
    instructor: "Dr. Sarah Johnson",
    category: "Programming",
    completedLabs: 1,
    totalLabs: 3,
    color: "purple",
  },
  {
    id: 2,
    slug: "web-development",
    title: "Web Development",
    description: "Build modern web pages using HTML, CSS, and JavaScript.",
    instructor: "Michael Brown",
    category: "Web Development",
    completedLabs: 0,
    totalLabs: 2,
    color: "blue",
  },
  {
    id: 3,
    slug: "computer-networks",
    title: "Computer Networks",
    description:
      "Study network configuration, addressing, and troubleshooting.",
    instructor: "Emily Wilson",
    category: "Networking",
    completedLabs: 0,
    totalLabs: 3,
    color: "green",
  },
];

export const mockAssignments: Assignment[] = [
  {
    id: 1,
    courseId: 1,
    title: "Variables and Data Types",
    description: "Create variables and convert values between data types.",
    difficulty: "Beginner",
    topic: "Programming Basics",
    xp: 100,
    status: "completed",
    languages: programmingLanguages,
  },
  {
    id: 2,
    courseId: 1,
    title: "Conditional Statements",
    description: "Use if and else branches to solve a grading problem.",
    difficulty: "Beginner",
    topic: "Control Flow",
    xp: 120,
    status: "in-progress",
    languages: programmingLanguages,
  },
  {
    id: 3,
    courseId: 1,
    title: "Functions and Parameters",
    description: "Create reusable functions with parameters and return values.",
    difficulty: "Intermediate",
    topic: "Functions",
    xp: 150,
    status: "not-started",
    languages: programmingLanguages,
  },
  {
    id: 4,
    courseId: 2,
    title: "Page Structure with HTML",
    description:
      "Build a profile page with a heading, a paragraph, a list, and a link.",
    difficulty: "Beginner",
    topic: "Web Basics",
    xp: 100,
    status: "not-started",
    languages: ["html"],
  },
  {
    id: 5,
    courseId: 2,
    title: "Styling with CSS",
    description:
      "Style a card with a selector, colors, spacing, and a flex or grid layout.",
    difficulty: "Beginner",
    topic: "Web Basics",
    xp: 100,
    status: "not-started",
    languages: ["css"],
  },
];

export const mockProgress: StudentProgress = {
  level: 3,
  xp: 340,
  nextLevelXp: 500,
  completedAssignments: 1,
  totalAssignments: 5,
};

export const mockStudent: StudentProfile = {
  name: "Alex Morgan",
  initials: "AM",
  email: "alex.morgan@example.edu",
  course: "Programming Foundations",
  streakDays: 5,
};
