import sys
import os

filepath = os.path.join(os.path.dirname(__file__), '..', 'static', 'css', 'custom.css')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_styles = """
/* Animation suite hien dai va tinh te */

/* 1. Modal bay len em ai */
@keyframes h2tModalSlideUp {
    0% {
        opacity: 0;
        transform: translate3d(0, 24px, 0) scale(0.97);
    }
    100% {
        opacity: 1;
        transform: translate3d(0, 0, 0) scale(1);
    }
}

.animate-modal-up,
.modal-slide-up {
    animation: h2tModalSlideUp 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* 2. Toast va ngan keo bay ngang tu phai sang */
@keyframes h2tSlideInRightSubtle {
    0% {
        opacity: 0;
        transform: translate3d(28px, 0, 0);
    }
    100% {
        opacity: 1;
        transform: translate3d(0, 0, 0);
    }
}

.animate-slide-right,
.toast-slide-right {
    animation: h2tSlideInRightSubtle 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* 3. Chu va the an hien theo nhip dieu */
@keyframes h2tFadeUp {
    0% {
        opacity: 0;
        transform: translate3d(0, 14px, 0);
    }
    100% {
        opacity: 1;
        transform: translate3d(0, 0, 0);
    }
}

.anim-fade-up {
    animation: h2tFadeUp 0.32s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.anim-delay-1 { animation-delay: 0.04s; }
.anim-delay-2 { animation-delay: 0.08s; }
.anim-delay-3 { animation-delay: 0.12s; }
.anim-delay-4 { animation-delay: 0.16s; }
.anim-delay-5 { animation-delay: 0.20s; }
.anim-delay-6 { animation-delay: 0.24s; }

/* 4. Hieu ung phat sang nen nhe nhang cho trang dang nhap va dang ky */
@keyframes h2tGlowFloat {
    0%, 100% {
        transform: translate3d(0, 0, 0) scale(1);
        opacity: 0.35;
    }
    50% {
        transform: translate3d(0, -10px, 0) scale(1.08);
        opacity: 0.6;
    }
}

.anim-glow-float {
    animation: h2tGlowFloat 5s ease-in-out infinite;
}

/* 5. Switch toggle cho bang dieu khien bao tri */
.toggle-switch-checkbox:checked + .toggle-switch-track {
    background-color: #e11d48;
}

.toggle-switch-checkbox:checked + .toggle-switch-track .toggle-switch-thumb {
    transform: translateX(1.5rem);
}

/* 6. Rang buoc: Giu tinh hoan toan cac muc kham benh EMR de tranh gay roi mat bac si */
.emr-static-zone,
.emr-static-zone *,
#emr-exam-workspace,
#emr-exam-workspace *,
.emr-clinical-form,
.emr-clinical-form *,
.emr-step-container,
.emr-step-container *,
body[data-page="admin_emr"] main,
body[data-page="admin_emr"] main * {
    animation: none !important;
    transition: none !important;
    transform: none !important;
}
"""

if "h2tModalSlideUp" not in content:
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(new_styles)
    print("Added clean modern animation suite to static/css/custom.css")
else:
    print("Animation suite already present")
