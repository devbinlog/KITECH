"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { Sidebar } from "@/components/ui/Sidebar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const { checkAuth } = useAuthStore();
  const [isReady, setIsReady] = useState(false);
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => { setMenuOpen(false); }, [pathname]);

  useEffect(() => {
    // 클라이언트에서만 실행
    const token = localStorage.getItem("token");
    const authStorage = localStorage.getItem("auth-storage");
    
    if (token && authStorage) {
      // 토큰과 스토리지 데이터가 있으면 인증됨
      checkAuth(); // Zustand 상태도 동기화
      setIsAuthed(true);
    } else {
      // 인증 안 됨 - 로그인 페이지로
      router.push("/login");
    }
    setIsReady(true);
  }, [checkAuth, router]);

  // 준비 안 됨 - 로딩
  if (!isReady) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // 인증 안 됨
  if (!isAuthed) {
    return null;
  }

  return (
    <div className="flex min-h-screen">
      <div className="hidden md:block"><Sidebar /></div>
      {menuOpen && <div className="fixed inset-0 z-40 md:hidden">
        <button type="button" aria-label="메뉴 닫기" className="absolute inset-0 bg-black/50" onClick={() => setMenuOpen(false)} />
        <div className="absolute inset-y-0 left-0 overflow-y-auto"><Sidebar /></div>
        <button type="button" aria-label="메뉴 닫기" title="닫기" onClick={() => setMenuOpen(false)} className="absolute top-3 right-3 p-2 bg-white rounded"><X size={20} /></button>
      </div>}
      <main aria-label="주요 콘텐츠" className="flex-1 min-w-0 p-4 md:p-6 bg-gray-50 overflow-auto">
        <button type="button" aria-label="메뉴 열기" aria-expanded={menuOpen} onClick={() => setMenuOpen(true)} className="md:hidden mb-4 p-2 border rounded bg-white"><Menu size={20} /></button>
        {children}
      </main>
    </div>
  );
}
