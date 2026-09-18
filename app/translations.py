"""
Translations module for the Smart Knowledge Gap System.

Supports English (default) and Arabic.
Usage in templates:
    {{ t('nav.home') }}
    {{ t('nav.teacher') }}
"""

TRANSLATIONS = {
    "en": {
        # Navigation
        "nav.home": "Home",
        "nav.teacher": "Teacher",
        "nav.dashboard": "My Dashboard",
        "nav.logout": "Logout",
        "nav.login": "Login",

        # Home page
        "home.eyebrow": "PERSONALIZED LEARNING PLATFORM",
        "home.title": "Discover what you know.",
        "home.title_accent": "Learn what you need.",
        "home.subtitle": "Assess your knowledge concept by concept, discover your learning gaps, and receive a personalized path built around your current mastery.",
        "home.start_card_title": "Start your learning journey",
        "home.start_card_subtitle": "Create your account and choose your learning track.",
        "home.already_have_account": "Already have an account?",
        "home.login_link": "Log in",

        # Form labels
        "form.name": "Student name",
        "form.email": "Email",
        "form.password": "Password",
        "form.age": "Age",
        "form.subject": "Subject",
        "form.level": "Level",
        "form.choose_subject": "Choose a subject",
        "form.choose_level": "Choose your level",
        "form.create_account": "Create Account & Start",

        # Assessment
        "assessment.eyebrow": "DIAGNOSTIC ASSESSMENT",
        "assessment.title": "Let's discover what you know.",
        "assessment.choose": "Choose the best answer",
        "assessment.continue": "Continue",
        "assessment.question": "Question",

        # Results
        "results.eyebrow": "ASSESSMENT COMPLETE",
        "results.title": "Your learning profile is ready.",
        "results.subtitle": "We analyzed your answers concept by concept and built a learning path around the areas that need the most attention.",
        "results.open_dashboard": "Open My Learning Dashboard",
        "results.knowledge_profile": "KNOWLEDGE PROFILE",
        "results.what_tells_us": "What your assessment tells us",
        "results.learning_priorities": "LEARNING PRIORITIES",
        "results.where_to_focus": "Where you should focus first",
        "results.learning_path": "PERSONALIZED LEARNING PATH",
        "results.your_journey": "Your recommended journey",
        "results.next_step": "NEXT STEP",
        "results.ready_learning": "Ready to start learning?",

        # Dashboard
        "dashboard.eyebrow": "STUDENT DASHBOARD",
        "dashboard.welcome": "Welcome back",
        "dashboard.overall_mastery": "Overall Mastery",
        "dashboard.strong_concepts": "Strong Concepts",
        "dashboard.knowledge_gaps": "Knowledge Gaps",
        "dashboard.practice_attempts": "Practice Attempts",
        "dashboard.achievements": "ACHIEVEMENTS",
        "dashboard.your_badges": "Your badges",
        "dashboard.download_pdf": "Download PDF Report",

        # Practice
        "practice.eyebrow": "PRACTICE MODE",
        "practice.submit": "Submit Practice",
        "practice.your_score": "YOUR SCORE",
        "practice.back_dashboard": "Back to Dashboard",

        # Learning Content
        "learning.eyebrow": "LEARNING CONTENT",
        "learning.study_then_practice": "Study this concept, then practice it to reinforce your understanding.",
        "learning.explanation": "Explanation",
        "learning.key_points": "Key Points",
        "learning.why_it_matters": "Why It Matters",
        "learning.step_by_step": "Step-by-Step",
        "learning.worked_examples": "Worked Examples",
        "learning.common_mistakes": "Common Mistakes",
        "learning.study_tips": "Study Tips",
        "learning.whats_next": "What's Next",
        "learning.start_practice": "Start Practice",

        # Login
        "login.eyebrow": "WELCOME BACK",
        "login.title": "Log in to continue",
        "login.title_accent": "your learning journey.",
        "login.subtitle": "Sign in with your email and password to access your learning dashboard, knowledge gaps, and personalized learning path.",
        "login.card_title": "Log in to your account",
        "login.card_subtitle": "Enter your email and password below.",
        "login.button": "Log In",
        "login.no_account": "Don't have an account?",
        "login.create_link": "Create one now",

        # Errors
        "error.404.title": "Oops! Page not found.",
        "error.404.message": "The page you are looking for doesn't exist or has been moved.",
        "error.500.title": "Something went wrong.",
        "error.500.message": "Our servers encountered an unexpected error. Please try again.",

        # Common
        "common.back_home": "Back to Home",
        "common.try_again": "Try Again",
        "common.loading": "Loading...",
    },

    "ar": {
        # Navigation
        "nav.home": "الرئيسية",
        "nav.teacher": "المعلم",
        "nav.dashboard": "لوحتي",
        "nav.logout": "تسجيل خروج",
        "nav.login": "تسجيل دخول",

        # Home page
        "home.eyebrow": "منصة تعلم شخصية",
        "home.title": "اكتشف ما تعرفه.",
        "home.title_accent": "تعلم ما تحتاجه.",
        "home.subtitle": "قيّم معرفتك مفهوماً بمفهوم، اكتشف فجواتك المعرفية، واحصل على مسار تعلم شخصي مبني على مستواك الحالي.",
        "home.start_card_title": "ابدأ رحلتك التعليمية",
        "home.start_card_subtitle": "أنشئ حسابك واختر مسارك التعليمي.",
        "home.already_have_account": "هل لديك حساب بالفعل؟",
        "home.login_link": "تسجيل دخول",

        # Form labels
        "form.name": "اسم الطالب",
        "form.email": "البريد الإلكتروني",
        "form.password": "كلمة المرور",
        "form.age": "السن",
        "form.subject": "المادة",
        "form.level": "المستوى",
        "form.choose_subject": "اختر مادة",
        "form.choose_level": "اختر مستواك",
        "form.create_account": "أنشئ حسابك وابدأ",

        # Assessment
        "assessment.eyebrow": "الاختبار التشخيصي",
        "assessment.title": "هيا نكتشف ما تعرفه.",
        "assessment.choose": "اختر الإجابة الأفضل",
        "assessment.continue": "متابعة",
        "assessment.question": "سؤال",

        # Results
        "results.eyebrow": "اكتمل الاختبار",
        "results.title": "ملفك التعليمي جاهز.",
        "results.subtitle": "حللنا إجاباتك مفهوماً بمفهوم، وبنينا مسار تعلم حول المجالات التي تحتاج أكبر اهتمام.",
        "results.open_dashboard": "افتح لوحة التعلم",
        "results.knowledge_profile": "الملف المعرفي",
        "results.what_tells_us": "ما يخبرنا به اختبارك",
        "results.learning_priorities": "أولويات التعلم",
        "results.where_to_focus": "أين يجب أن تركز أولاً",
        "results.learning_path": "مسار التعلم الشخصي",
        "results.your_journey": "رحلتك المقترحة",
        "results.next_step": "الخطوة التالية",
        "results.ready_learning": "هل أنت جاهز للتعلم؟",

        # Dashboard
        "dashboard.eyebrow": "لوحة الطالب",
        "dashboard.welcome": "أهلاً بك",
        "dashboard.overall_mastery": "الإتقان الكلي",
        "dashboard.strong_concepts": "المفاهيم القوية",
        "dashboard.knowledge_gaps": "الفجوات المعرفية",
        "dashboard.practice_attempts": "محاولات التمرين",
        "dashboard.achievements": "الإنجازات",
        "dashboard.your_badges": "شاراتك",
        "dashboard.download_pdf": "تحميل التقرير PDF",

        # Practice
        "practice.eyebrow": "وضع التمرين",
        "practice.submit": "إرسال التمرين",
        "practice.your_score": "نتيجتك",
        "practice.back_dashboard": "العودة للوحة",

        # Learning Content
        "learning.eyebrow": "محتوى التعلم",
        "learning.study_then_practice": "ادرس هذا المفهوم، ثم تدرّب عليه لتثبيت فهمك.",
        "learning.explanation": "الشرح",
        "learning.key_points": "النقاط الأساسية",
        "learning.why_it_matters": "لماذا هو مهم",
        "learning.step_by_step": "خطوة بخطوة",
        "learning.worked_examples": "أمثلة محلولة",
        "learning.common_mistakes": "الأخطاء الشائعة",
        "learning.study_tips": "نصائح للمذاكرة",
        "learning.whats_next": "ما التالي",
        "learning.start_practice": "ابدأ التمرين",

        # Login
        "login.eyebrow": "أهلاً بعودتك",
        "login.title": "سجّل الدخول لمتابعة",
        "login.title_accent": "رحلتك التعليمية.",
        "login.subtitle": "سجّل الدخول بالبريد الإلكتروني وكلمة المرور للوصول إلى لوحة التعلم وفجواتك المعرفية ومسارك الشخصي.",
        "login.card_title": "تسجيل الدخول",
        "login.card_subtitle": "أدخل بريدك الإلكتروني وكلمة المرور أدناه.",
        "login.button": "دخول",
        "login.no_account": "ليس لديك حساب؟",
        "login.create_link": "أنشئ حساباً الآن",

        # Errors
        "error.404.title": "عذراً! الصفحة غير موجودة.",
        "error.404.message": "الصفحة التي تبحث عنها غير موجودة أو تم نقلها.",
        "error.500.title": "حدث خطأ ما.",
        "error.500.message": "واجهت خوادمنا خطأً غير متوقع. يرجى المحاولة مرة أخرى.",

        # Common
        "common.back_home": "العودة للرئيسية",
        "common.try_again": "حاول مرة أخرى",
        "common.loading": "جاري التحميل...",
    },
}


def get_text(lang, key, default=None):
    """
    Get a translated string by language and key.

    Falls back to English if the key is missing in the requested language.
    Falls back to the key itself if missing everywhere.
    """
    if lang not in TRANSLATIONS:
        lang = "en"

    translations = TRANSLATIONS[lang]

    if key in translations:
        return translations[key]

    # Fallback to English
    if lang != "en" and key in TRANSLATIONS["en"]:
        return TRANSLATIONS["en"][key]

    return default if default is not None else key


SUPPORTED_LANGUAGES = ["en", "ar"]
