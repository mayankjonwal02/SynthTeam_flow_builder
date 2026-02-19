"use client";

import { useEffect, useRef, useState } from "react";
import Script from "next/script";

/**
 * Scroll-animated Spline 3D viewer.
 *
 * How it works:
 *   • The outer <section> is 200vh tall.
 *   • Inside is a sticky viewport-height container that stays pinned.
 *   • As the user scrolls through the extra 100vh, the animation plays.
 *   • The animation progress goes 0→1 over that entire scroll distance.
 *   • Only AFTER progress hits 1 does the sticky container un-pin and
 *     the page content below starts to scroll into view.
 *
 * This gives the illusion that scrolling is "locked" while the 3D
 * asset moves to center, and only then does the rest of the page appear.
 */
export default function SplineHero({
  children,
}: {
  children: React.ReactNode;
}) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0); // 0 → 1

  useEffect(() => {
    const onScroll = () => {
      if (!sectionRef.current) return;
      const rect = sectionRef.current.getBoundingClientRect();
      const sectionHeight = sectionRef.current.offsetHeight;
      const viewportHeight = window.innerHeight;

      // The scroll distance available for the animation is:
      //   sectionHeight - viewportHeight  (the "extra" height beyond one screen)
      // progress 0 = haven't scrolled at all
      // progress 1 = scrolled exactly to the point where the sticky un-pins
      const scrollDistance = sectionHeight - viewportHeight;
      if (scrollDistance <= 0) return;

      const raw = -rect.top / scrollDistance;
      setProgress(Math.min(Math.max(raw, 0), 1));
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // ── derived transforms ──
  const scale = 1.0 + progress * 0.3; // 1.0 → 1.3
  const translateXPct = (1 - progress) * 25; // 25% → 0% (right → center)
  const textOpacity = Math.max(1 - progress * 2.5, 0); // fades out in first 40% of scroll
  const textTranslateX = -progress * 60;

  return (
    <>
      <Script
        type="module"
        src="https://unpkg.com/@splinetool/viewer@1.12.58/build/spline-viewer.js"
        strategy="afterInteractive"
      />

      {/* 200vh = 1 screen visible + 1 screen of "scroll runway" for animation */}
      <section ref={sectionRef} className="relative" style={{ height: "200vh" }}>
        {/* ambient glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-indigo-600/[0.07] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-40 right-1/4 w-[400px] h-[400px] bg-violet-600/[0.05] rounded-full blur-[100px] pointer-events-none" />

        {/* ── sticky inner — pinned for the entire scroll runway ── */}
        <div className="sticky top-0 h-screen overflow-hidden">
          {/* ── Text layer ── */}
          <div
            className="absolute inset-0 z-10 flex items-center"
            style={{ top: "4rem" }}
          >
            <div className="max-w-7xl mx-auto px-6 w-full">
              <div
                className="max-w-xl text-center lg:text-left"
                style={{
                  opacity: textOpacity,
                  transform: `translateX(${textTranslateX}px)`,
                  transition: "opacity 0.05s, transform 0.05s",
                  pointerEvents: textOpacity < 0.3 ? "none" : "auto",
                }}
              >
                {children}
              </div>
            </div>
          </div>

          {/* ── 3D asset layer ── */}
          <div
            className="absolute left-0 right-0 flex items-center justify-center pointer-events-none"
            style={{
              top: "4rem",
              bottom: 0,
              transform: `translateX(${translateXPct}%) translateY(${progress * 8}%) scale(${scale})`,
              transformOrigin: "center 40%",
              transition: "transform 0.08s linear",
            }}
          >
            {/*
              Hack to hide "Built with Spline" watermark:
              1. Outer wrapper clips with overflow:hidden and is the visible size.
              2. Inner container is taller/wider so the bottom-right watermark
                 is pushed outside the clipped area.
              3. Gradient overlays as backup for any leftover pixels.
            */}
            <div
              className="w-[550px] h-[550px] lg:w-[620px] lg:h-[620px] relative pointer-events-auto"
              style={{ overflow: "hidden" }}
            >
              {/* @ts-expect-error — Spline web component */}
              <spline-viewer
                url="https://prod.spline.design/AaWe14-wXVFMdtcm/scene.splinecode"
                style={{
                  width: "calc(100% + 40px)",
                  height: "calc(100% + 50px)",
                  position: "absolute",
                  top: 0,
                  left: 0,
                }}
              />
              {/* Gradient overlay — covers any remaining watermark remnant */}
              <div
                className="absolute bottom-0 right-0 z-[999]"
                style={{
                  width: "220px",
                  height: "70px",
                  background: "linear-gradient(135deg, transparent 0%, #06060a 35%)",
                  pointerEvents: "none",
                }}
              />
              {/* Bottom strip — extra safety */}
              <div
                className="absolute bottom-0 left-0 right-0 z-[999]"
                style={{
                  height: "12px",
                  background: "#06060a",
                  pointerEvents: "none",
                }}
              />
              {/* Right strip — extra safety */}
              <div
                className="absolute top-0 bottom-0 right-0 z-[999]"
                style={{
                  width: "12px",
                  background: "#06060a",
                  pointerEvents: "none",
                }}
              />
            </div>
          </div>

          {/* bottom fade */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#06060a] to-transparent pointer-events-none z-20" />
        </div>
      </section>
    </>
  );
}
