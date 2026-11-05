export const ABOUT_PATH = "/about";

// The page to return to from About. Opening About directly has none, so it
// falls back to the home page. Only paths inside this site are accepted.
export const getReturnPath = (state: unknown): string => {
  const from = (state as { from?: unknown } | null)?.from;
  const isInternalPath =
    typeof from === "string" && from.startsWith("/") && !from.startsWith("//");

  return isInternalPath ? from : "/";
};
