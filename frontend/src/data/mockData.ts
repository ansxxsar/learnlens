import type { Assignment, StudentProfile, StudentProgress } from "../types";

export const mockAssignments: Assignment[] = [
  {
    id: 1,
    title: "Python Variables and Data Types",
    description:
      "Create variables and convert values between Python data types.",
    difficulty: "Beginner",
    topic: "Python Basics",
    xp: 100,
    status: "completed",
  },
  {
    id: 2,
    title: "Conditional Statements",
    description: "Use if, elif, and else to solve a grading problem.",
    difficulty: "Beginner",
    topic: "Control Flow",
    xp: 120,
    status: "in-progress",
  },
  {
    id: 3,
    title: "Functions and Parameters",
    description: "Create reusable functions with parameters and return values.",
    difficulty: "Intermediate",
    topic: "Functions",
    xp: 150,
    status: "not-started",
  },
];

export const mockProgress: StudentProgress = {
  level: 3,
  xp: 340,
  nextLevelXp: 500,
  completedAssignments: 1,
  totalAssignments: 3,
};

export const mockStudent: StudentProfile = {
  name: "Alex Morgan",
  initials: "AM",
  email: "alex.morgan@example.edu",
  course: "Python Foundations",
  streakDays: 5,
};
