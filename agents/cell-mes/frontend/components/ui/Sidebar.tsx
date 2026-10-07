"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Database,
  Settings,
  Package,
  Workflow,
  Truck,
  Cpu,
  Factory,
  ClipboardList,
  BarChart3,
  Calendar,
  Zap,
  SlidersHorizontal,
  Shield,
  FileText,
  CheckCircle,
  TrendingUp,
  Activity,
  AlertTriangle,
  Search,
  Bot,
  LogOut,
  ChevronRight,
  Clock,
  Bell,
} from "lucide-react";
import { ExternalLink } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { KitechLogo } from "@/components/ui/KitechLogo";
import clsx from "clsx";

interface MenuItem {
  href?: string;
  label: string;
  icon: LucideIcon;
  children?: MenuItem[];
  /** True for external links — renders <a target="_blank"> instead of next/link. */
  external?: boolean;
}


const menuItems: MenuItem[] = [
  { href: "/", label: "대시보드", icon: LayoutDashboard },
  {
    label: "기준정보",
    icon: Database,
    children: [
      { href: "/master/processes", label: "표준공정", icon: Settings },
      { href: "/master/products", label: "제품관리", icon: Package },
      { href: "/master/routings", label: "라우팅설계", icon: Workflow },
      { href: "/master/scenarios", label: "물류시나리오", icon: Truck },
      { href: "/master/equipments", label: "설비관리", icon: Cpu },
      { href: "/master/cells", label: "Cell 관리", icon: Factory },
      {
        href: process.env.NEXT_PUBLIC_N8N_EDITOR_URL || "http://localhost:5678",
        label: "n8n 에디터",
        icon: Workflow,
        external: true,
      },
    ],
  },
  {
    label: "생산관리",
    icon: Factory,
    children: [
      { href: "/production/orders", label: "작업지시", icon: ClipboardList },
      { href: "/production/results", label: "생산실적", icon: BarChart3 },
      { href: "/downtime", label: "다운타임", icon: Clock },
      { href: "/alarms", label: "알람관리", icon: Bell },
    ],
  },
  {
    label: "스케줄러",
    icon: Calendar,
    children: [
      { href: "/scheduler", label: "스케줄 현황", icon: Calendar },
      { href: "/scheduler/execute", label: "스케줄 실행", icon: Zap },
      { href: "/scheduler/settings", label: "솔버 설정", icon: SlidersHorizontal },
    ],
  },
  {
    label: "품질관리",
    icon: Shield,
    children: [
      { href: "/quality", label: "품질 대시보드", icon: Shield },
      { href: "/quality/inspection-plans", label: "검사계획", icon: FileText },
      { href: "/quality/inspection-results", label: "측정결과", icon: CheckCircle },
      { href: "/quality/spc", label: "SPC 차트", icon: TrendingUp },
      { href: "/quality/ncr", label: "NCR 관리", icon: AlertTriangle },
    ],
  },
  {
    label: "분석리포트",
    icon: TrendingUp,
    children: [
      { href: "/analytics", label: "분석 대시보드", icon: TrendingUp },
      { href: "/analytics/equipment", label: "설비 가동률", icon: Activity },
      { href: "/analytics/lot-trace", label: "Lot 추적", icon: Search },
    ],
  },
];

function isItemActive(href: string, pathname: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

function isGroupActive(item: MenuItem, pathname: string): boolean {
  if (!item.children) return false;
  return item.children.some(
    (child) => child.href && isItemActive(child.href, pathname)
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const [openSections, setOpenSections] = useState<Set<string>>(new Set());

  // 현재 경로에 해당하는 그룹 자동 펼침
  useEffect(() => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      menuItems.forEach((item) => {
        if (item.children && isGroupActive(item, pathname)) {
          next.add(item.label);
        }
      });
      return next;
    });
  }, [pathname]);

  const toggleSection = (label: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-gray-700 flex items-center gap-3">
        <KitechLogo size={36} className="shrink-0" ariaLabel="KITECH 한국생산기술연구원" />
        <div className="min-w-0">
          <h1 className="text-xl font-bold leading-tight">Cell-MES</h1>
          <p className="text-xs text-gray-400">Manufacturing Execution System</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <ul className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;

            // 단일 메뉴 (children 없음)
            if (!item.children) {
              const isActive = item.href ? isItemActive(item.href, pathname) : false;
              return (
                <li key={item.label}>
                  <Link
                    href={item.href!}
                    className={clsx(
                      "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                      isActive
                        ? "bg-primary-600 text-white"
                        : "text-gray-300 hover:bg-gray-800 hover:text-white"
                    )}
                  >
                    <Icon size={20} />
                    <span>{item.label}</span>
                  </Link>
                </li>
              );
            }

            // 그룹 메뉴 (children 있음)
            const isOpen = openSections.has(item.label);
            const groupActive = isGroupActive(item, pathname);

            return (
              <li key={item.label}>
                <button
                  onClick={() => toggleSection(item.label)}
                  className={clsx(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                    groupActive
                      ? "text-white"
                      : "text-gray-400 hover:bg-gray-800 hover:text-white"
                  )}
                >
                  <Icon size={20} />
                  <span className="flex-1 text-left text-sm font-medium">{item.label}</span>
                  <ChevronRight
                    size={16}
                    className={clsx(
                      "transition-transform duration-200",
                      isOpen && "rotate-90"
                    )}
                  />
                </button>

                {/* 하위 메뉴 */}
                <ul
                  className={clsx(
                    "overflow-hidden transition-[max-height,opacity] duration-200 ease-in-out pl-4 space-y-0.5",
                    isOpen ? "max-h-96 opacity-100 mt-1" : "max-h-0 opacity-0"
                  )}
                >
                  {item.children.map((child) => {
                    const ChildIcon = child.icon;
                    const childActive = child.href && !child.external
                      ? isItemActive(child.href, pathname)
                      : false;

                    // 외부 링크 child (예: n8n 에디터)
                    if (child.external) {
                      return (
                        <li key={child.label}>
                          <a
                            href={child.href!}
                            target="_blank"
                            rel="noopener noreferrer"
                            title={`${child.label} (외부 사이트, 새 탭)`}
                            aria-label={`${child.label} (새 탭에서 열기)`}
                            className="flex items-center gap-3 px-3 py-1.5 rounded-md text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
                          >
                            <ChildIcon size={16} />
                            <span className="flex-1">{child.label}</span>
                            <ExternalLink size={12} className="opacity-60" />
                          </a>
                        </li>
                      );
                    }

                    return (
                      <li key={child.href}>
                        <Link
                          href={child.href!}
                          className={clsx(
                            "flex items-center gap-3 px-3 py-1.5 rounded-md transition-colors text-sm",
                            childActive
                              ? "bg-primary-600 text-white"
                              : "text-gray-400 hover:bg-gray-800 hover:text-white"
                          )}
                        >
                          <ChildIcon size={16} />
                          <span>{child.label}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </li>
            );
          })}
        </ul>

        {/* AI Assistant */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <Link
            href="/chat"
            className={clsx(
              "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
              pathname === "/chat"
                ? "bg-gradient-to-r from-primary-600 to-secondary-600 text-white"
                : "text-gray-300 hover:bg-gray-800 hover:text-white"
            )}
          >
            <Bot size={20} />
            <span>AI 어시스턴트</span>
            <span className="ml-auto px-1.5 py-0.5 text-[10px] font-medium bg-primary-500 text-white rounded">
              NEW
            </span>
          </Link>
        </div>
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">{user?.username}</p>
            <p className="text-xs text-gray-400">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded"
            title="로그아웃"
          >
            <LogOut size={20} />
          </button>
        </div>
      </div>
    </aside>
  );
}
