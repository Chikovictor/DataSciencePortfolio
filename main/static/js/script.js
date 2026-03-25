document.addEventListener("DOMContentLoaded", () => {
    const storageKey = "portfolio-theme";
    const defaultTheme = "dark";
    const body = document.body;
    const themeToggle = document.getElementById("theme-toggle");
    const menuToggle = document.getElementById("menu-toggle");
    const navPanel = document.getElementById("nav-panel");
    const navLinks = document.querySelectorAll(".nav-links a");
    const header = document.querySelector(".site-header");

    const applyTheme = (theme) => {
        body.setAttribute("data-theme", theme);
        if (!themeToggle) {
            return;
        }
        const isDark = theme === "dark";
        themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
        themeToggle.setAttribute("title", isDark ? "Switch to light mode" : "Switch to dark mode");
    };

    const getStoredTheme = () => {
        try {
            return localStorage.getItem(storageKey);
        } catch (_) {
            return null;
        }
    };

    const setStoredTheme = (theme) => {
        try {
            localStorage.setItem(storageKey, theme);
        } catch (_) {
            // Ignore storage errors.
        }
    };

    const savedTheme = getStoredTheme();
    const systemPrefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = savedTheme || (systemPrefersDark ? "dark" : defaultTheme);
    applyTheme(initialTheme);

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const currentTheme = body.getAttribute("data-theme") || defaultTheme;
            const nextTheme = currentTheme === "dark" ? "light" : "dark";
            applyTheme(nextTheme);
            setStoredTheme(nextTheme);
        });
    }

    const closeMenu = () => {
        if (!navPanel || !menuToggle) {
            return;
        }
        navPanel.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
    };

    if (menuToggle && navPanel) {
        menuToggle.addEventListener("click", () => {
            const isOpen = navPanel.classList.toggle("open");
            menuToggle.setAttribute("aria-expanded", String(isOpen));
        });

        document.addEventListener("click", (event) => {
            if (window.innerWidth > 900 || !navPanel.classList.contains("open")) {
                return;
            }
            if (!event.target.closest(".navbar")) {
                closeMenu();
            }
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 900) {
                closeMenu();
            }
        });
    }

    const smoothScrollTo = (selector) => {
        const target = document.querySelector(selector);
        if (!target) {
            return;
        }
        const headerOffset = header ? header.offsetHeight : 0;
        const top = target.getBoundingClientRect().top + window.scrollY - headerOffset + 1;
        window.scrollTo({ top, behavior: "smooth" });
    };

    navLinks.forEach((link) => {
        link.addEventListener("click", (event) => {
            const href = link.getAttribute("href");
            if (!href || !href.startsWith("#")) {
                return;
            }
            if (!document.querySelector(href)) {
                return;
            }
            event.preventDefault();
            smoothScrollTo(href);
            closeMenu();
        });
    });

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        if (anchor.closest(".nav-links")) {
            return;
        }

        anchor.addEventListener("click", (event) => {
            const href = anchor.getAttribute("href");
            if (!href || href === "#" || !document.querySelector(href)) {
                return;
            }
            event.preventDefault();
            smoothScrollTo(href);
        });
    });

    const carousel = document.querySelector("[data-review-carousel]");
    const prevButton = document.querySelector("[data-carousel-prev]");
    const nextButton = document.querySelector("[data-carousel-next]");

    if (carousel && prevButton && nextButton) {
        const updateButtons = () => {
            const maxScrollLeft = carousel.scrollWidth - carousel.clientWidth - 2;
            prevButton.disabled = carousel.scrollLeft <= 1;
            nextButton.disabled = carousel.scrollLeft >= maxScrollLeft;
        };

        const scrollByCard = (direction) => {
            const card = carousel.querySelector(".testimonial-card");
            const step = card ? card.getBoundingClientRect().width + 16 : 320;
            carousel.scrollBy({ left: direction * step, behavior: "smooth" });
        };

        prevButton.addEventListener("click", () => scrollByCard(-1));
        nextButton.addEventListener("click", () => scrollByCard(1));
        carousel.addEventListener("scroll", updateButtons, { passive: true });
        window.addEventListener("resize", updateButtons);
        updateButtons();
    }

    const caseCards = document.querySelectorAll("[data-case-link]");
    caseCards.forEach((card) => {
        card.addEventListener("click", (event) => {
            if (event.target.closest("a, button")) {
                return;
            }
            const targetUrl = card.dataset.caseLink;
            if (targetUrl) {
                window.open(targetUrl, "_blank", "noopener,noreferrer");
            }
        });
    });

    const autoDismissTimers = new WeakMap();
    const clearAutoDismiss = (element) => {
        if (!element) {
            return;
        }
        const timerId = autoDismissTimers.get(element);
        if (timerId) {
            window.clearTimeout(timerId);
            autoDismissTimers.delete(element);
        }
    };

    const scheduleAutoDismiss = (element, delayMs = 5000) => {
        if (!element) {
            return;
        }
        clearAutoDismiss(element);
        element.style.setProperty("--dismiss-ms", `${delayMs}ms`);
        element.classList.add("is-timed");
        const hideTimer = window.setTimeout(() => {
            element.classList.add("is-hiding");
            window.setTimeout(() => {
                element.hidden = true;
                element.textContent = "";
                element.classList.remove("is-hiding", "is-timed", "success", "error", "warning");
            }, 250);
        }, delayMs);
        autoDismissTimers.set(element, hideTimer);
    };

    const setStatus = (statusElement, message, tone) => {
        if (!statusElement) {
            return;
        }
        clearAutoDismiss(statusElement);
        statusElement.classList.remove("is-hiding", "is-timed", "success", "error", "warning");
        statusElement.style.removeProperty("--dismiss-ms");
        statusElement.textContent = message || "";
        if (tone === "success" || tone === "error" || tone === "warning") {
            statusElement.classList.add(tone);
        }
        statusElement.hidden = !message;
        const delayAttr = Number.parseInt(statusElement.dataset.autoDismiss || "5000", 10);
        const delayMs = Number.isFinite(delayAttr) ? delayAttr : 5000;
        if ((tone === "success" || tone === "error" || tone === "warning") && message) {
            scheduleAutoDismiss(statusElement, delayMs);
        }
    };

    const clearAjaxFieldErrors = (formElement) => {
        formElement.querySelectorAll(".ajax-field-error").forEach((node) => node.remove());
        formElement.querySelectorAll("[aria-invalid='true']").forEach((node) => {
            node.setAttribute("aria-invalid", "false");
        });
    };

    const addFieldError = (formElement, fieldName, message) => {
        const fieldInput = formElement.querySelector(`[name="${fieldName}"]`);
        if (!fieldInput) {
            return;
        }
        const wrapper = fieldInput.closest(".field");
        if (!wrapper) {
            return;
        }
        fieldInput.setAttribute("aria-invalid", "true");
        const errorNode = document.createElement("small");
        errorNode.className = "field-error ajax-field-error";
        errorNode.textContent = message;
        wrapper.appendChild(errorNode);
    };

    const clearFieldErrorForInput = (fieldInput) => {
        if (!fieldInput) {
            return;
        }
        fieldInput.setAttribute("aria-invalid", "false");
        const wrapper = fieldInput.closest(".field");
        if (!wrapper) {
            return;
        }
        wrapper.querySelectorAll(".ajax-field-error").forEach((node) => node.remove());
    };

    const applyRenderedAt = (formElement, payload) => {
        const renderedAt = formElement.querySelector('input[name="rendered_at"]');
        if (!renderedAt) {
            return;
        }
        const nextTimestamp =
            typeof payload?.rendered_at === "number" ? payload.rendered_at : Date.now() / 1000;
        renderedAt.value = String(nextTimestamp);
    };

    const setupAjaxForm = (config) => {
        const formElement = document.getElementById(config.formId);
        if (!formElement) {
            return;
        }
        const statusElement = document.getElementById(config.statusId);
        const submitButton = formElement.querySelector('button[type="submit"]');
        const labelElement = submitButton ? submitButton.querySelector(".btn-label") : null;
        const defaultSubmitLabel = labelElement
            ? labelElement.textContent
            : submitButton
              ? submitButton.textContent
              : "Submit";
        const loadingSubmitLabel = String(
            submitButton?.dataset.loadingLabel || defaultSubmitLabel || "Sending"
        )
            .trim()
            .replace(/[.\u2026]+$/g, "")
            .trim();

        formElement.addEventListener("input", (event) => {
            const target = event.target;
            if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) {
                return;
            }
            clearFieldErrorForInput(target);
        });

        formElement.addEventListener("change", (event) => {
            const target = event.target;
            if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) {
                return;
            }
            clearFieldErrorForInput(target);
        });

        formElement.addEventListener("submit", async (event) => {
            event.preventDefault();
            clearAjaxFieldErrors(formElement);
            setStatus(statusElement, "", "");

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.classList.add("is-loading");
                submitButton.setAttribute("aria-busy", "true");
                if (labelElement) {
                    labelElement.textContent = loadingSubmitLabel;
                } else {
                    submitButton.textContent = loadingSubmitLabel;
                }
            }

            const formData = new FormData(formElement);
            if (config.submitField && !formData.has(config.submitField)) {
                formData.append(config.submitField, "1");
            }
            const csrfToken =
                formElement.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "";

            try {
                const response = await fetch(formElement.action, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": csrfToken,
                    },
                    body: formData,
                });
                const payload = await response.json().catch(() => null);

                if (!response.ok || !payload || payload.success !== true) {
                    const fieldErrors = payload?.field_errors || payload?.errors || {};
                    const hasFieldErrors = Object.keys(fieldErrors).length > 0;
                    Object.keys(fieldErrors).forEach((fieldName) => {
                        const firstError = Array.isArray(fieldErrors[fieldName])
                            ? fieldErrors[fieldName][0]
                            : "";
                        if (firstError) {
                            addFieldError(formElement, fieldName, firstError);
                        }
                    });

                    const nonFieldErrors = Array.isArray(payload?.non_field_errors)
                        ? payload.non_field_errors
                        : [];
                    const failureMessage =
                        (typeof payload?.message === "string" && payload.message) ||
                        nonFieldErrors[0] ||
                        (hasFieldErrors ? "" : config.errorFallbackMessage);
                    if (failureMessage) {
                        setStatus(statusElement, failureMessage, "error");
                    }
                    applyRenderedAt(formElement, payload);
                    return;
                }

                setStatus(
                    statusElement,
                    payload.message || config.successFallbackMessage,
                    "success"
                );
                formElement.reset();
                applyRenderedAt(formElement, payload);
            } catch (_) {
                setStatus(statusElement, "Network error. Please try again in a moment.", "error");
            } finally {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.classList.remove("is-loading");
                    submitButton.removeAttribute("aria-busy");
                    if (labelElement) {
                        labelElement.textContent = defaultSubmitLabel;
                    } else {
                        submitButton.textContent = defaultSubmitLabel;
                    }
                }
            }
        });
    };

    setupAjaxForm({
        formId: "contact-form",
        statusId: "contact-form-status",
        submitField: "contact_submit",
        successFallbackMessage: "Your message has been sent!",
        errorFallbackMessage: "Message could not be sent right now. Please try again.",
    });

    setupAjaxForm({
        formId: "review-form",
        statusId: "review-form-status",
        submitField: "review_submit",
        successFallbackMessage: "Your review has been submitted!",
        errorFallbackMessage: "Review could not be submitted right now. Please try again.",
    });

    document.querySelectorAll(".form-status[data-auto-dismiss]").forEach((messageNode) => {
        const delay = Number.parseInt(messageNode.dataset.autoDismiss || "5000", 10);
        scheduleAutoDismiss(messageNode, Number.isFinite(delay) ? delay : 5000);
    });

    // Lightbox Logic
    const lightboxModal = document.getElementById("lightbox-modal");
    const lightboxImg = document.getElementById("lightbox-image");
    const lightboxCaption = document.getElementById("lightbox-caption");
    const lightboxTriggers = document.querySelectorAll(".lightbox-trigger");
    const lightboxCloses = document.querySelectorAll("[data-lightbox-close]");

    if (lightboxModal && lightboxImg) {
        lightboxTriggers.forEach(trigger => {
            trigger.addEventListener("click", () => {
                const src = trigger.getAttribute("data-lightbox-src");
                const caption = trigger.getAttribute("data-lightbox-caption");
                if (src) {
                    lightboxImg.src = src;
                    if (lightboxCaption) {
                        lightboxCaption.textContent = caption || "";
                    }
                    lightboxModal.setAttribute("aria-hidden", "false");
                    document.body.style.overflow = "hidden";
                }
            });
        });

        const closeLightbox = () => {
            lightboxModal.setAttribute("aria-hidden", "true");
            document.body.style.overflow = "";
            setTimeout(() => {
                lightboxImg.src = "";
            }, 300);
        };

        lightboxCloses.forEach(closeBtn => {
            closeBtn.addEventListener("click", closeLightbox);
        });

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && lightboxModal.getAttribute("aria-hidden") === "false") {
                closeLightbox();
            }
        });
    }

    const revealElements = document.querySelectorAll(".reveal");
    if (revealElements.length) {
        body.classList.add("anim-ready");
    }

    if (!("IntersectionObserver" in window)) {
        revealElements.forEach((element) => element.classList.add("is-visible"));
        return;
    }

    const revealObserver = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            });
        },
        {
            threshold: 0.16,
            rootMargin: "0px 0px -40px 0px",
        }
    );

    revealElements.forEach((element) => revealObserver.observe(element));
});
