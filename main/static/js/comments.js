document.addEventListener("DOMContentLoaded", () => {
    const interactionsRoot = document.querySelector("[data-insight-interactions]");
    const reactionRoot = document.querySelector("[data-reaction-url]");
    const commentForm = document.getElementById("comment-form");
    const commentsThread = document.getElementById("comments-thread");
    const commentStatus = document.getElementById("comment-form-status");
    const commentTotal = document.querySelector("[data-comment-total]");
    const replyTarget = document.getElementById("reply-target");
    const cancelReplyButton = document.getElementById("comment-reply-cancel");
    const reactionStatus = document.getElementById("reaction-status");
    const identityForm = document.getElementById("identity-form");
    const identityInput = document.getElementById("identity-name");
    const identityStatus = document.getElementById("identity-status");

    if (!interactionsRoot || !commentForm) {
        return;
    }

    const IDENTITY_STORAGE_KEY = "portfolio_display_name";
    const IDENTITY_COOKIE_NAME = "portfolio_display_name";
    const csrfToken =
        document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || "";
    const hiddenUserNameInput = commentForm.querySelector('input[name="user_name"]');
    const commentFields = commentForm.querySelectorAll("input, textarea, button[type='submit']");
    const reactionButtons = reactionRoot
        ? reactionRoot.querySelectorAll("[data-reaction-emoji]")
        : [];

    let identityName = "";
    const autoDismissTimers = new WeakMap();

    const normalizeName = (value) => (typeof value === "string" ? value.trim() : "");
    const isValidIdentity = (value) => normalizeName(value).length >= 2;

    const readCookie = (name) => {
        const matches = document.cookie.match(
            new RegExp(`(?:^|; )${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}=([^;]*)`)
        );
        return matches ? decodeURIComponent(matches[1]) : "";
    };

    const writeCookie = (name, value, days = 30) => {
        const maxAge = days * 24 * 60 * 60;
        document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAge}; path=/; samesite=lax`;
    };

    const readStoredIdentity = () => {
        const fromDataset = normalizeName(interactionsRoot.dataset.initialName || "");
        if (fromDataset) {
            return fromDataset;
        }

        const fromSession = (() => {
            try {
                return sessionStorage.getItem(IDENTITY_STORAGE_KEY) || "";
            } catch (_) {
                return "";
            }
        })();

        if (fromSession) {
            return normalizeName(fromSession);
        }

        return normalizeName(readCookie(IDENTITY_COOKIE_NAME));
    };

    const setStoredIdentity = (value) => {
        try {
            sessionStorage.setItem(IDENTITY_STORAGE_KEY, value);
        } catch (_) {
            // Ignore storage errors.
        }
        writeCookie(IDENTITY_COOKIE_NAME, value);
    };

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

    const setStatus = (element, message, tone) => {
        if (!element) {
            return;
        }
        clearAutoDismiss(element);
        element.classList.remove("is-hiding", "is-timed", "success", "error", "warning");
        element.style.removeProperty("--dismiss-ms");
        element.textContent = message || "";
        element.hidden = !message;
        if (!message) {
            return;
        }
        if (tone === "success" || tone === "error" || tone === "warning") {
            element.classList.add(tone);
            const delayAttr = Number.parseInt(element.dataset.autoDismiss || "5000", 10);
            scheduleAutoDismiss(element, Number.isFinite(delayAttr) ? delayAttr : 5000);
        }
    };

    const toggleInteractionState = (enabled) => {
        if (!commentForm) {
            return;
        }
        commentForm.classList.toggle("is-locked", !enabled);

        commentFields.forEach((field) => {
            if (!(field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement || field instanceof HTMLButtonElement)) {
                return;
            }
            if (field.name === "csrfmiddlewaretoken" || field.name === "honeypot" || field.name === "rendered_at" || field.name === "parent_id" || field.name === "user_name") {
                return;
            }
            field.disabled = !enabled;
        });

        reactionButtons.forEach((button) => {
            if (button instanceof HTMLButtonElement) {
                button.disabled = !enabled;
            }
        });
    };

    const applyIdentity = (nextName, options = {}) => {
        const normalized = normalizeName(nextName);
        const valid = isValidIdentity(normalized);
        identityName = valid ? normalized : "";

        if (identityInput) {
            identityInput.value = identityName || normalized;
        }
        if (hiddenUserNameInput) {
            hiddenUserNameInput.value = identityName;
        }

        toggleInteractionState(valid);

        if (valid && options.persist !== false) {
            setStoredIdentity(identityName);
        }

        if (!options.silent) {
            if (valid) {
                setStatus(identityStatus, `Signed in as ${identityName}.`, "success");
            } else {
                setStatus(
                    identityStatus,
                    "Enter at least 2 characters in your name to comment or react.",
                    "error"
                );
            }
        }
        return valid;
    };

    const clearFieldErrors = (formElement) => {
        formElement.querySelectorAll(".ajax-field-error").forEach((node) => node.remove());
        formElement.querySelectorAll("[aria-invalid='true']").forEach((field) => {
            field.setAttribute("aria-invalid", "false");
        });
    };

    const addFieldError = (formElement, fieldName, message) => {
        const fieldInput = formElement.querySelector(`[name="${fieldName}"]`);
        if (!fieldInput) {
            return;
        }
        fieldInput.setAttribute("aria-invalid", "true");
        const wrapper = fieldInput.closest(".field");
        if (!wrapper) {
            return;
        }
        const error = document.createElement("small");
        error.className = "field-error ajax-field-error";
        error.textContent = message;
        wrapper.appendChild(error);
    };

    const escapeText = (value) => (typeof value === "string" ? value : "");

    const buildCommentNode = (comment) => {
        const article = document.createElement("article");
        article.className = "comment-item";
        article.dataset.commentId = String(comment.id);

        const avatar = document.createElement("span");
        avatar.className = "comment-avatar";
        avatar.textContent = escapeText(comment.avatar_text || "U");

        const body = document.createElement("div");
        body.className = "comment-body";

        const header = document.createElement("header");
        header.className = "comment-header";

        const strong = document.createElement("strong");
        strong.textContent = escapeText(comment.user_name);

        const time = document.createElement("time");
        time.dateTime = escapeText(comment.created_at);
        time.textContent = escapeText(comment.created_label);

        header.appendChild(strong);
        header.appendChild(time);

        const content = document.createElement("p");
        content.className = "comment-content";
        content.textContent = escapeText(comment.content);

        const replyButton = document.createElement("button");
        replyButton.type = "button";
        replyButton.className = "comment-reply-btn";
        replyButton.dataset.replyTo = String(comment.id);
        replyButton.dataset.replyName = escapeText(comment.user_name);
        replyButton.textContent = "Reply";

        body.appendChild(header);
        body.appendChild(content);
        body.appendChild(replyButton);

        article.appendChild(avatar);
        article.appendChild(body);

        if (Array.isArray(comment.replies) && comment.replies.length > 0) {
            const replies = document.createElement("div");
            replies.className = "comment-replies";
            comment.replies.forEach((child) => {
                replies.appendChild(buildCommentNode(child));
            });
            article.appendChild(replies);
        }

        return article;
    };

    const renderComments = (comments) => {
        if (!commentsThread) {
            return;
        }
        commentsThread.innerHTML = "";

        if (!Array.isArray(comments) || comments.length === 0) {
            const empty = document.createElement("p");
            empty.className = "comments-empty";
            empty.textContent = "No comments yet. Start the discussion.";
            commentsThread.appendChild(empty);
            return;
        }

        comments.forEach((comment) => {
            commentsThread.appendChild(buildCommentNode(comment));
        });
    };

    const updateCommentTotal = (count) => {
        if (!commentTotal) {
            return;
        }
        if (Number.isFinite(Number(count))) {
            commentTotal.textContent = String(count);
        }
    };

    const clearReplyState = () => {
        const parentInput = commentForm.querySelector('input[name="parent_id"]');
        if (parentInput) {
            parentInput.value = "";
        }
        if (replyTarget) {
            replyTarget.hidden = true;
            replyTarget.textContent = "";
        }
        if (cancelReplyButton) {
            cancelReplyButton.hidden = true;
        }
    };

    const setReplyState = (commentId, userName) => {
        const parentInput = commentForm.querySelector('input[name="parent_id"]');
        if (parentInput) {
            parentInput.value = String(commentId);
        }
        if (replyTarget) {
            replyTarget.hidden = false;
            replyTarget.textContent = `Replying to ${userName}`;
        }
        if (cancelReplyButton) {
            cancelReplyButton.hidden = false;
        }
        const contentField = commentForm.querySelector('textarea[name="content"]');
        contentField?.focus();
    };

    const setRenderedAt = (nextValue) => {
        const renderedAt = commentForm.querySelector('input[name="rendered_at"]');
        if (!renderedAt) {
            return;
        }
        if (typeof nextValue === "number") {
            renderedAt.value = String(nextValue);
            return;
        }
        renderedAt.value = String(Date.now() / 1000);
    };

    const loadComments = async () => {
        const commentsUrl = interactionsRoot.dataset.commentsUrl;
        if (!commentsUrl) {
            return;
        }

        try {
            const response = await fetch(commentsUrl, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const payload = await response.json().catch(() => null);
            if (!response.ok || !payload || payload.success !== true) {
                return;
            }
            renderComments(payload.comments || []);
            updateCommentTotal(payload.count);
        } catch (_) {
            // Keep current comments if refresh fails.
        }
    };

    identityForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        const candidate = normalizeName(identityInput?.value || "");
        applyIdentity(candidate);
    });

    identityInput?.addEventListener("input", () => {
        setStatus(identityStatus, "", "");
    });

    commentsThread?.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
            return;
        }
        const replyButton = target.closest("[data-reply-to]");
        if (!replyButton) {
            return;
        }

        if (!isValidIdentity(identityName)) {
            setStatus(identityStatus, "Set your name first to reply.", "error");
            identityInput?.focus();
            return;
        }

        const commentId = replyButton.getAttribute("data-reply-to");
        const replyName = replyButton.getAttribute("data-reply-name") || "this user";
        if (!commentId) {
            return;
        }
        setReplyState(commentId, replyName);
    });

    cancelReplyButton?.addEventListener("click", () => {
        clearReplyState();
    });

    const postUrl = interactionsRoot.dataset.commentPostUrl || commentForm.action;
    const submitButton = commentForm.querySelector('button[type="submit"]');

    commentForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearFieldErrors(commentForm);
        setStatus(commentStatus, "", "");

        if (!isValidIdentity(identityName)) {
            setStatus(commentStatus, "Please enter your name before posting.", "error");
            identityInput?.focus();
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add("is-loading");
            submitButton.setAttribute("aria-busy", "true");
        }

        if (hiddenUserNameInput) {
            hiddenUserNameInput.value = identityName;
        }
        const formData = new FormData(commentForm);
        formData.set("user_name", identityName);

        try {
            const response = await fetch(postUrl, {
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
                Object.keys(fieldErrors).forEach((fieldName) => {
                    const firstError = Array.isArray(fieldErrors[fieldName])
                        ? fieldErrors[fieldName][0]
                        : "";
                    if (firstError) {
                        addFieldError(commentForm, fieldName, firstError);
                    }
                });

                const nonFieldErrors = Array.isArray(payload?.non_field_errors)
                    ? payload.non_field_errors
                    : [];
                const errorMessage =
                    payload?.message ||
                    nonFieldErrors[0] ||
                    "Comment could not be posted right now.";
                setStatus(commentStatus, errorMessage, "error");
                setRenderedAt(payload?.rendered_at);
                return;
            }

            if (payload.identity_name) {
                applyIdentity(payload.identity_name, { silent: true });
            }
            setStatus(commentStatus, payload.message || "Comment posted successfully.", "success");
            commentForm.reset();
            if (hiddenUserNameInput) {
                hiddenUserNameInput.value = identityName;
            }
            clearReplyState();
            setRenderedAt(payload.rendered_at);
            renderComments(payload.comments || []);
            updateCommentTotal(payload.count);
        } catch (_) {
            setStatus(commentStatus, "Network error. Please try again in a moment.", "error");
        } finally {
            if (submitButton) {
                submitButton.disabled = !isValidIdentity(identityName);
                submitButton.classList.remove("is-loading");
                submitButton.removeAttribute("aria-busy");
            }
        }
    });

    if (reactionRoot) {
        const reactionUrl = reactionRoot.dataset.reactionUrl;

        const updateReactionUi = (counts, activeEmojis) => {
            const activeSet = new Set(Array.isArray(activeEmojis) ? activeEmojis : []);
            reactionButtons.forEach((button) => {
                const emoji = button.getAttribute("data-reaction-emoji") || "";
                const countNode = button.querySelector(`[data-reaction-count="${emoji}"]`);
                if (countNode && counts && Object.prototype.hasOwnProperty.call(counts, emoji)) {
                    countNode.textContent = String(counts[emoji]);
                }
                button.classList.toggle("is-active", activeSet.has(emoji));
            });
        };

        reactionButtons.forEach((button) => {
            button.addEventListener("click", async () => {
                if (!reactionUrl) {
                    return;
                }
                if (!isValidIdentity(identityName)) {
                    setStatus(reactionStatus, "Please enter your name before reacting.", "error");
                    identityInput?.focus();
                    return;
                }

                const emoji = button.getAttribute("data-reaction-emoji");
                if (!emoji || button.dataset.busy === "1") {
                    return;
                }

                button.dataset.busy = "1";
                button.setAttribute("aria-busy", "true");
                setStatus(reactionStatus, "", "");

                const payload = new FormData();
                payload.append("emoji", emoji);
                payload.append("user_name", identityName);

                try {
                    const response = await fetch(reactionUrl, {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "X-Requested-With": "XMLHttpRequest",
                            "X-CSRFToken": csrfToken,
                        },
                        body: payload,
                    });

                    const result = await response.json().catch(() => null);
                    if (!response.ok || !result || result.success !== true) {
                        const errorMessage =
                            result?.message || "Reaction could not be updated right now.";
                        setStatus(reactionStatus, errorMessage, "error");
                        return;
                    }
                    if (result.identity_name) {
                        applyIdentity(result.identity_name, { silent: true });
                    }
                    updateReactionUi(result.counts, result.active_emojis);
                } catch (_) {
                    setStatus(reactionStatus, "Network error. Please try again.", "error");
                } finally {
                    delete button.dataset.busy;
                    button.removeAttribute("aria-busy");
                }
            });
        });
    }

    applyIdentity(readStoredIdentity(), { silent: true });
    loadComments();
});
