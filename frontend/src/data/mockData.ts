import type {
  StudentProfile,
  StudentProgress,
} from "../types";

export const mockProgress: StudentProgress = {
  level: 3,
  xp: 340,
  nextLevelXp: 500,
  completedAssignments: 1,
  totalAssignments: 5,
};

export const mockStudent: StudentProfile = {
  accountType: "student",
  courses: [],
  photoUrl: null,
  preferredLanguage: null,
  memberSince: "2026-01-01T00:00:00Z",
  name: "Alex Morgan",
  initials: "AM",
  email: "alex.morgan@example.edu",
  course: "Programming Foundations",
  streakDays: 5,
};
