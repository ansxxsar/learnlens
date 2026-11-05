import { Link, useLocation } from "react-router-dom";
import { ABOUT_PATH, getReturnPath } from "../../utils/aboutNavigation";

// Opens About, and from About returns to the page the visitor came from.
export function BrandLink() {
  const location = useLocation();
  const isOnAbout = location.pathname === ABOUT_PATH;

  return (
    <Link
      className="brand"
      to={isOnAbout ? getReturnPath(location.state) : ABOUT_PATH}
      state={
        isOnAbout
          ? undefined
          : { from: `${location.pathname}${location.search}${location.hash}` }
      }
      aria-label={isOnAbout ? "Back to your last page" : "About LearnLens"}
    >
      <span className="brand__icon">L</span>
      <span>LearnLens</span>
    </Link>
  );
}
