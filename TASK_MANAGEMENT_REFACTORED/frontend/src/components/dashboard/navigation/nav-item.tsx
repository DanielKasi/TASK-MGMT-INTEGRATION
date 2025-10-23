import { ChevronDown, ChevronRight } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useSelector } from "react-redux";

import { Button } from "@/platform/v1/components";
import { useMobile } from "@/hooks/use-mobile";
import { selectSideBarOpened } from "@/store/miscellaneous/selectors-context-aware";
import { NavItem } from "@/types/other";
import { useModuleNavigation } from "@/hooks/use-module-navigation";

export const NavItemComponent = ({
  item,
  isMobileView = false,
  index,
  expandedItems,
  onExpand,
  onToggle,
}: {
  item: NavItem;
  expandedItems: { [key: string]: boolean };
  isMobileView: boolean;
  index: number;
  onExpand: (item_title: string) => void;
  onToggle: () => void;
}) => {
  const pathname = usePathname();
  const isActive = item.submenu
    ? item.submenu.some((sub) => pathname === sub.href)
    : pathname === item.href;
  const isExpanded = expandedItems[item.title];
  const isSideBarOpen = useSelector(selectSideBarOpened);
  const isMobile = useMobile();
  const router = useModuleNavigation();

  return (
    <div key={`${item.title}-${index}`} className="w-full py-1">
      <Button
        disabled={!item.href || (item.href.startsWith("#") && !item.submenu?.length)}
        variant="ghost"
        className={`w-full !rounded-xl flex items-center px-2 !py-6 text-sm font-medium
          text-sidebar-foreground
          hover:bg-sidebar-primary hover:text-sidebar-primary-foreground
          ${isActive ? "bg-sidebar-primary text-sidebar-primary-foreground" : ""}
          ${isSideBarOpen ? "justify-between" : "justify-center"}
        `}
        onClick={() => {
          if (item.submenu) {
            onExpand(item.title);
            !isSideBarOpen && onToggle();
          } else {
            router.push(item.href);
            if (isMobileView) {
              onToggle();
            }
          }
        }}
      >
        <div className="flex items-center space-x-2 relative">
          {item.icon}
          {isSideBarOpen && <span className="truncate">{item.title}</span>}
        </div>
        {isSideBarOpen && item.submenu && (
          isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
        )}
      </Button>

      {item.submenu && isExpanded && (
        <div className="ml-6 flex flex-col mt-2 border-l-2 border-sidebar-border bg-sidebar-accent/30">
          {isSideBarOpen &&
            item.submenu.map((sub, idx) => (
              <Button
                key={`${sub.href}-${idx}`}
                variant="ghost"
                className={`w-full !rounded-none !text-left flex items-center px-2 !py-4 text-sm
                  text-sidebar-foreground
                  hover:bg-sidebar-primary hover:text-sidebar-primary-foreground
                  ${
                    pathname === sub.href
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : ""
                  }
                  ${!sub.href || sub.href.startsWith("#") ? "opacity-60 cursor-not-allowed" : ""}
                `}
                onClick={() => {
                  router.push(sub.href);
                  if (isMobileView) {
                    onToggle();
                  }
                }}
              >
                <span className="!w-full !text-left !bg-transparent truncate">{sub.title}</span>
              </Button>
            ))}
        </div>
      )}
    </div>
  );
};