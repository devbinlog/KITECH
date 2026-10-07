'use client';

import { useState, useRef, useEffect, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';

interface PopoverProps {
  trigger: ReactNode;
  children: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Popover({ trigger, children, position = 'bottom' }: PopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const togglePopover = () => {
    if (!isOpen && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      let x = rect.left;
      let y = rect.bottom + 8;

      // Adjust position to stay in viewport
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      
      if (x + 280 > viewportWidth) {
        x = viewportWidth - 290;
      }
      if (y + 200 > viewportHeight) {
        y = rect.top - 208;
      }

      setCoords({ x: Math.max(10, x), y });
    }
    setIsOpen(!isOpen);
  };

  const popoverStyle: React.CSSProperties = {
    position: 'fixed',
    left: coords.x,
    top: coords.y,
    zIndex: 9999,
  };

  return (
    <>
      <div
        ref={triggerRef}
        onClick={(e) => {
          e.stopPropagation();
          togglePopover();
        }}
        style={{ display: 'contents' }}
      >
        {trigger}
      </div>
      {mounted && isOpen && createPortal(
        <div ref={popoverRef} style={popoverStyle}>
          <div className="bg-white rounded-lg shadow-xl border border-gray-200 min-w-[280px] max-w-sm">
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-2 right-2 p-1 hover:bg-gray-100 rounded"
            >
              <X size={14} />
            </button>
            {children}
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

export default Popover;
