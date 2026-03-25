document.addEventListener("DOMContentLoaded", () => {
    const carousels = document.querySelectorAll("[data-profile-carousel]");
    if (!carousels.length) {
        return;
    }

    const syncHeroCarouselHeights = () => {
        const useSync = window.matchMedia("(min-width: 1081px)").matches;
        carousels.forEach((carousel) => {
            const heroGrid = carousel.closest(".hero-grid");
            const heroCopy = heroGrid?.querySelector(".hero-copy");
            if (!heroCopy || !useSync) {
                carousel.style.removeProperty("--hero-copy-height");
                return;
            }
            const copyHeight = Math.round(heroCopy.getBoundingClientRect().height);
            if (copyHeight > 0) {
                carousel.style.setProperty("--hero-copy-height", `${copyHeight}px`);
            }
        });
    };

    carousels.forEach((carousel) => {
        const track = carousel.querySelector("[data-profile-track]");
        const slides = Array.from(carousel.querySelectorAll("[data-profile-slide]"));
        const dots = Array.from(carousel.querySelectorAll("[data-profile-dot]"));
        const prevButton = carousel.querySelector("[data-profile-prev]");
        const nextButton = carousel.querySelector("[data-profile-next]");
        const controls = carousel.querySelector("[data-profile-controls]");

        if (!track || slides.length === 0) {
            return;
        }

        let activeIndex = 0;
        let intervalId = null;
        const intervalMs = Number.parseInt(carousel.dataset.profileInterval || "4500", 10);
        const hasMultipleSlides = slides.length > 1;

        const applyState = () => {
            track.style.transform = `translateX(-${activeIndex * 100}%)`;
            slides.forEach((slide, index) => {
                const isActive = index === activeIndex;
                slide.classList.toggle("is-active", isActive);
                slide.setAttribute("aria-hidden", String(!isActive));
            });

            dots.forEach((dot, index) => {
                dot.classList.toggle("is-active", index === activeIndex);
                dot.setAttribute("aria-current", index === activeIndex ? "true" : "false");
            });
        };

        const goTo = (nextIndex) => {
            if (!hasMultipleSlides) {
                return;
            }
            const normalizedIndex =
                (nextIndex + slides.length) % slides.length;
            activeIndex = normalizedIndex;
            applyState();
        };

        const startAuto = () => {
            if (!hasMultipleSlides || !Number.isFinite(intervalMs) || intervalMs < 1000) {
                return;
            }
            window.clearInterval(intervalId);
            intervalId = window.setInterval(() => {
                goTo(activeIndex + 1);
            }, intervalMs);
        };

        const stopAuto = () => {
            if (!intervalId) {
                return;
            }
            window.clearInterval(intervalId);
            intervalId = null;
        };

        prevButton?.addEventListener("click", () => {
            goTo(activeIndex - 1);
        });

        nextButton?.addEventListener("click", () => {
            goTo(activeIndex + 1);
        });

        dots.forEach((dot, index) => {
            dot.addEventListener("click", () => {
                goTo(index);
            });
        });

        if (!hasMultipleSlides) {
            controls?.setAttribute("hidden", "hidden");
        } else {
            carousel.addEventListener("mouseenter", stopAuto);
            carousel.addEventListener("mouseleave", startAuto);
            carousel.addEventListener("focusin", stopAuto);
            carousel.addEventListener("focusout", startAuto);
            document.addEventListener("visibilitychange", () => {
                if (document.hidden) {
                    stopAuto();
                } else {
                    startAuto();
                }
            });
        }

        applyState();
        startAuto();
    });

    syncHeroCarouselHeights();
    window.addEventListener("resize", syncHeroCarouselHeights);
    window.addEventListener("load", syncHeroCarouselHeights);
});
