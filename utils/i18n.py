from fastapi import Request
from typing import Dict

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # --- Users / Auth ---
        "user_already_registered": "This email is already registered",
        "user_not_found": "User not found",
        "inactive_user": "User is inactive",
        "invalid_credentials": "Invalid email or password",
        "email_not_verified": "Email not verified",
        "too_many_attempts": "Too many attempts, please try again later",
        "invalid_oauth2_token": "Invalid OAuth2 token",
        "email_already_in_use": "This email is already in use",
        "password_too_weak": "Password is too weak",
        "invalid_email_format": "Invalid email format",
        "permission_denied": "Permission denied",
        "logout_successful": "Logout successful",
        "password_updated": "Password updated successfully",
        "incorrect_password": "Incorrect password",

        # --- Users / Verification / OTP ---
        "verification_failed": "Verification failed",
        "verification_sent": "Verification code has been sent",
        "verification_resent": "Verification code has been resent",
        "otp_resend_failed": "Failed to resend OTP, please try again",
        "otp_verification_failed": "OTP verification failed",
        "code_confirmed": "Code confirmed",
        "code_resent": "Verification code resent",

        # --- Users / Profile ---
        "profile_updated": "Profile updated successfully",

        # --- Users / Comments ---
        "comment_created": "Comment created successfully",
        "comment_updated": "Comment updated successfully",
        "comment_deleted": "Comment deleted successfully",
        "comment_not_found": "Comment not found",

        # --- Common Errors / Other ---
        "internal_error": "Internal server error",
        "forbidden": "Forbidden",
        "no_answer_feedback": "No answer",
        "unknown_chart_type": "Unknown chart type",

        # --- Tests / Listening ---
        "no_listening_tests": "No listening tests available",
        "listening_test_not_found": "Listening test not found",
        "listening_session_not_found": "Listening session not found",
        "listening_part_not_found": "Listening part not found",
        "listening_section_not_found": "Listening section not found",
        "parent_listening_not_found": "Parent listening test not found",
        "parent_part_not_found": "Parent listening part not found",
        "parent_section_not_found": "Parent listening section not found",
        "listening_already_completed": "Listening test already completed",
        "cannot_cancel_session": "Cannot cancel this session",

        # --- Tests / Reading ---
        "no_reading_tests": "No reading tests available",
        "reading_not_found": "Reading test not found",
        "no_passages": "No passages available for reading test",
        "passage_not_found": "Passage not found",
        "passage_number_exists": "Passage with this number already exists",
        "reading_already_completed": "Reading test already completed",
        "reading_not_completed": "Reading test is not completed",
        "reading_cancelled": "Reading session cancelled successfully",
        "insufficient_tokens": "Not enough tokens for reading test",
        "test_generation_failed": "Failed to generate reading test",
        "test_parsing_failed": "Failed to parse generated test",
        "not_enough_passages": "Not enough passages in the generated test",
        "invalid_passage": "Invalid passage",
        "session_completed_successfully": "Reading session completed successfully",
        "session_restarted_successfully": "Reading session restarted successfully",
        "transaction_description": "Tokens deducted for test: {price}",

        # --- Tests / Writing ---
        "no_writing_tests": "No writing tests available",
        "writing_test_not_found": "Writing test not found",
        "writing_test_not_completed": "Writing test is not completed",
        "writing_analysis_failed": "Failed to analyse writing test",
        "writing_analysis_invalid_format": "Invalid analysis format",

        # --- Tests / Session Common ---
        "session_not_found": "Session not found",
        "session_not_completed": "Session is not completed",
        "session_already_completed": "Session already completed",
        "session_already_completed_or_cancelled": "Session already completed or cancelled",
        "session_cancelled": "Session cancelled successfully",
        "session_already_cancelled": "Session already cancelled",
        "session_expired": "Session expired",
        "session_in_progress": "Session is still in progress",
        "session_restarted": "Session restarted",
        "cannot_restart_session": "Cannot restart active session",

        # --- Tests / Answers & Questions ---
        "answers_required": "Answers are required",
        "invalid_answer_format": "Invalid answer format",
        "question_not_found": "Question not found",
        "answers_submitted": "Answers submitted successfully",
        "not_all_audio_uploaded": "Not all audio files uploaded",
        "invalid_question_count": "Invalid question count",
        "question_parsing_failed": "Failed parsing questions",
        "question_generation_failed": "Failed to generate questions",
        "part1_audio_required": "Part 1 audio is required",

        # --- Analyses ---
        "analysis_not_found": "Failed to generate analysis",
        "analysis_started": "Analysis started, please try again later",

        # --- Payments / Tokens ---
        "not_enough_tokens": "You don't have enough tokens.",
        "payment_not_found": "Payment not found",
        "payment_already_exists": "Payment for this tariff already exists and is active",
        "payment_confirmed": "Payment confirmed and tokens added",
        "payment_failed": "Payment failed",
        "test_type_not_found": "Test type not found",

        # --- Payments / New ---
        "tariff_not_found": "Tariff not found",
        "payment_exists": "Active payment already exists",
        "atm_error": "Payment service error: {error}",
        "invalid_callback": "Invalid callback data",
        "invalid_callback (no JSON)": "Invalid callback (no JSON)",
        "tokens_for_tariff": "Tokens for {tariff_name}",
        "payment_successful": "Payment Successful",
        "you_bought_tariff": "You bought {tariff_name}.",
        "tokens_credited": "{tokens} tokens credited.",
    },
    "ru": {
        # --- Users / Auth ---
        "user_already_registered": "Этот email уже зарегистрирован",
        "user_not_found": "Пользователь не найден",
        "inactive_user": "Пользователь неактивен",
        "invalid_credentials": "Неверный логин или пароль",
        "email_not_verified": "Email не подтверждён",
        "too_many_attempts": "Слишком много попыток, попробуйте позже",
        "invalid_oauth2_token": "Неверный OAuth2 токен",
        "email_already_in_use": "Этот email уже используется",
        "password_too_weak": "Пароль слишком простой",
        "invalid_email_format": "Некорректный формат email",
        "permission_denied": "Доступ запрещён",
        "logout_successful": "Вы успешно вышли из системы",
        "password_updated": "Пароль успешно обновлён",
        "incorrect_password": "Неверный пароль",

        # --- Users / Verification / OTP ---
        "verification_failed": "Ошибка подтверждения",
        "verification_sent": "Код подтверждения отправлен",
        "verification_resent": "Код подтверждения отправлен повторно",
        "otp_resend_failed": "Не удалось повторно отправить OTP, попробуйте снова",
        "otp_verification_failed": "Ошибка подтверждения OTP",
        "code_confirmed": "Код подтверждён",
        "code_resent": "Код подтверждения отправлен повторно",

        # --- Users / Profile ---
        "profile_updated": "Профиль успешно обновлён",

        # --- Users / Comments ---
        "comment_created": "Комментарий успешно создан",
        "comment_updated": "Комментарий успешно обновлён",
        "comment_deleted": "Комментарий успешно удалён",
        "comment_not_found": "Комментарий не найден",

        # --- Common Errors / Other ---
        "internal_error": "Внутренняя ошибка сервера",
        "forbidden": "Доступ запрещён",
        "no_answer_feedback": "Нет ответа",
        "unknown_chart_type": "Неизвестный тип диаграммы",

        # --- Tests / Listening ---
        "no_listening_tests": "Нет доступных тестов прослушивания",
        "listening_test_not_found": "Тест прослушивания не найден",
        "listening_session_not_found": "Сессия прослушивания не найдена",
        "listening_part_not_found": "Часть прослушивания не найдена",
        "listening_section_not_found": "Раздел прослушивания не найден",
        "parent_listening_not_found": "Родительский тест прослушивания не найден",
        "parent_part_not_found": "Родительская часть прослушивания не найдена",
        "parent_section_not_found": "Родительский раздел прослушивания не найден",
        "listening_already_completed": "Тест прослушивания уже завершён",
        "cannot_cancel_session": "Эту сессию нельзя отменить",

        # --- Tests / Reading ---
        "no_reading_tests": "Нет доступных тестов чтения",
        "reading_not_found": "Тест чтения не найден",
        "no_passages": "Нет доступных отрывков для теста чтения",
        "passage_not_found": "Отрывок не найден",
        "passage_number_exists": "Отрывок с этим номером уже существует",
        "reading_already_completed": "Тест чтения уже завершён",
        "reading_not_completed": "Тест чтения не завершён",
        "reading_cancelled": "Сессия чтения успешно отменена",
        "insufficient_tokens": "Недостаточно токенов для теста чтения",
        "test_generation_failed": "Не удалось создать тест чтения",
        "test_parsing_failed": "Не удалось обработать созданный тест",
        "not_enough_passages": "Недостаточно отрывков в созданном тесте",
        "invalid_passage": "Неверный отрывок",
        "session_completed_successfully": "Сессия чтения успешно завершена",
        "session_restarted_successfully": "Сессия чтения успешно перезапущена",
        "transaction_description": "Списаны токены за тест: {price}",

        # --- Tests / Writing ---
        "no_writing_tests": "Нет доступных тестов по письму",
        "writing_test_not_found": "Тест по письму не найден",
        "writing_test_not_completed": "Тест по письму не завершён",
        "writing_analysis_failed": "Не удалось проанализировать тест по письму",
        "writing_analysis_invalid_format": "Некорректный формат анализа",

        # --- Tests / Session Common ---
        "session_not_found": "Сессия не найдена",
        "session_not_completed": "Сессия не завершена",
        "session_already_completed": "Сессия уже завершена",
        "session_already_completed_or_cancelled": "Сессия уже завершена или отменена",
        "session_cancelled": "Сессия успешно отменена",
        "session_already_cancelled": "Сессия уже отменена",
        "session_expired": "Сессия истекла",
        "session_in_progress": "Сессия ещё не завершена",
        "session_restarted": "Сессия успешно перезапущена",
        "cannot_restart_session": "Нельзя перезапустить активную сессию",

        # --- Tests / Answers & Questions ---
        "answers_required": "Необходимо отправить ответы",
        "invalid_answer_format": "Неверный формат ответа",
        "question_not_found": "Вопрос не найден",
        "answers_submitted": "Ответы успешно отправлены",
        "not_all_audio_uploaded": "Не все аудиофайлы загружены",
        "invalid_question_count": "Некорректное количество вопросов",
        "question_parsing_failed": "Ошибка разбора вопросов",
        "question_generation_failed": "Не удалось сгенерировать вопросы",
        "part1_audio_required": "Необходимо загрузить аудио для части 1",

        # --- Analyses ---
        "analysis_not_found": "Не удалось сгенерировать анализ",
        "analysis_started": "Анализ запущен, попробуйте позже",

        # --- Payments / Tokens ---
        "not_enough_tokens": "У вас недостаточно токенов.",
        "payment_not_found": "Платеж не найден",
        "payment_already_exists": "Платеж за этот тариф уже существует и активен",
        "payment_confirmed": "Платеж подтверждён и токены добавлены",
        "payment_failed": "Платеж не прошел",
        "test_type_not_found": "Тип теста не найден",

        # --- Payments / New ---
        "tariff_not_found": "Тариф не найден",
        "payment_exists": "Активная подписка уже существует",
        "atm_error": "Ошибка платёжного сервиса: {error}",
        "invalid_callback": "Некорректные данные обратного вызова",
        "invalid_callback (no JSON)": "Некорректные данные обратного вызова (нет JSON)",
        "tokens_for_tariff": "Токены за {tariff_name}",
        "payment_successful": "Платеж успешно выполнен",
        "you_bought_tariff": "Вы купили {tariff_name}.",
        "tokens_credited": "{tokens} токенов зачислено.",
    },
    "uz": {
        # --- Users / Auth ---
        "user_already_registered": "Bu email allaqachon ro'yxatdan o'tgan",
        "user_not_found": "Foydalanuvchi topilmadi",
        "inactive_user": "Foydalanuvchi faol emas",
        "invalid_credentials": "Login yoki parol noto‘g‘ri",
        "email_not_verified": "Email tasdiqlanmagan",
        "too_many_attempts": "Juda ko'p urinishlar, iltimos keyinroq urinib ko'ring",
        "invalid_oauth2_token": "Noto'g'ri OAuth2 token",
        "email_already_in_use": "Bu email allaqachon ishlatilmoqda",
        "password_too_weak": "Parol juda oddiy",
        "invalid_email_format": "Email formati noto'g'ri",
        "permission_denied": "Ruxsat yo'q",
        "logout_successful": "Tizimdan muvaffaqiyatli chiqdingiz",
        "password_updated": "Parol muvaffaqiyatli yangilandi",
        "incorrect_password": "Parol noto'g'ri",

        # --- Users / Verification / OTP ---
        "verification_failed": "Tasdiqlashda xato",
        "verification_sent": "Tasdiqlash kodi yuborildi",
        "verification_resent": "Tasdiqlash kodi qayta yuborildi",
        "otp_resend_failed": "OTPni qayta yuborishda xato, iltimos qayta urinib ko'ring",
        "otp_verification_failed": "OTPni tasdiqlashda xato",
        "code_confirmed": "Kod tasdiqlandi",
        "code_resent": "Tasdiqlash kodi yuborildi",

        # --- Users / Profile ---
        "profile_updated": "Profil muvaffaqiyatli yangilandi",

        # --- Users / Comments ---
        "comment_created": "Izoh muvaffaqiyatli yaratildi",
        "comment_updated": "Izoh muvaffaqiyatli yangilandi",
        "comment_deleted": "Izoh muvaffaqiyatli o'chirildi",
        "comment_not_found": "Izoh topilmadi",

        # --- Common Errors / Other ---
        "internal_error": "Ichki server xatosi",
        "forbidden": "Ruxsat yo'q",
        "no_answer_feedback": "Javob yo'q",
        "unknown_chart_type": "Noma'lum diagramma turi",

        # --- Tests / Listening ---
        "no_listening_tests": "Tinglash testlari mavjud emas",
        "listening_test_not_found": "Tinglash testi topilmadi",
        "listening_session_not_found": "Tinglash sessiyasi topilmadi",
        "listening_part_not_found": "Tinglash qismi topilmadi",
        "listening_section_not_found": "Tinglash bo‘limi topilmadi",
        "parent_listening_not_found": "Tinglash testi topilmadi",
        "parent_part_not_found": "Tinglash qismi topilmadi",
        "parent_section_not_found": "Tinglash bo‘limi topilmadi",
        "listening_already_completed": "Tinglash testi allaqachon yakunlangan",
        "cannot_cancel_session": "Bu sessiyani bekor qilib bo'lmaydi",

        # --- Tests / Reading ---
        "no_reading_tests": "O'qish testlari mavjud emas",
        "reading_not_found": "O'qish testi topilmadi",
        "no_passages": "O'qish testi uchun mavjud parchalar yo'q",
        "passage_not_found": "Parcha topilmadi",
        "passage_number_exists": "Bu raqamli parcha allaqachon mavjud",
        "reading_already_completed": "O'qish testi allaqachon yakunlangan",
        "reading_not_completed": "O'qish testi yakunlanmagan",
        "reading_cancelled": "O'qish sessiyasi muvaffaqiyatli bekor qilindi",
        "insufficient_tokens": "O'qish testi uchun yetarli tokenlar yo'q",
        "test_generation_failed": "O'qish testini yaratishda xato",
        "test_parsing_failed": "Yaratilgan testni tahlil qilishda xato",
        "not_enough_passages": "Yaratilgan testda yetarli parchalar yo'q",
        "invalid_passage": "Noto'g'ri parcha",
        "session_completed_successfully": "O'qish sessiyasi muvaffaqiyatli yakunlandi",
        "session_restarted_successfully": "O'qish sessiyasi muvaffaqiyatli qayta boshlandi",
        "transaction_description": "Test uchun tokenlar yechib olindi: {price}",

        # --- Tests / Writing ---
        "no_writing_tests": "Yozish testlari mavjud emas",
        "writing_test_not_found": "Yozish testi topilmadi",
        "writing_test_not_completed": "Yozish testi yakunlanmagan",
        "writing_analysis_failed": "Yozish testini tahlil qilishda xato",
        "writing_analysis_invalid_format": "Noto'g'ri tahlil formati",

        # --- Tests / Session Common ---
        "session_not_found": "Sessiya topilmadi",
        "session_not_completed": "Sessiya yakunlanmagan",
        "session_already_completed": "Sessiya allaqachon yakunlangan",
        "session_already_completed_or_cancelled": "Sessiya allaqachon yakunlangan yoki bekor qilingan",
        "session_cancelled": "Sessiya muvaffaqiyatli bekor qilindi",
        "session_already_cancelled": "Sessiya allaqachon bekor qilingan",
        "session_expired": "Sessiya muddati tugadi",
        "session_in_progress": "Sessiya hali tugamagan",
        "session_restarted": "Sessiya muvaffaqiyatli qayta boshlandi",
        "cannot_restart_session": "Faol sessiyani qayta boshlash mumkin emas",

        # --- Tests / Answers & Questions ---
        "answers_required": "Javoblarni yuborish kerak",
        "invalid_answer_format": "Javob formati noto'g'ri",
        "question_not_found": "Savol topilmadi",
        "answers_submitted": "Javoblar muvaffaqiyatli yuborildi",
        "not_all_audio_uploaded": "Hamma audio fayllar yuklanmagan",
        "invalid_question_count": "Savollar soni noto'g'ri",
        "question_parsing_failed": "Savollarni tahlil qilishda xato",
        "question_generation_failed": "Savollarni yaratishda xato",
        "part1_audio_required": "1-qism uchun audio yuklash kerak",

        # --- Analyses ---
        "analysis_not_found": "Tahlilni yaratib bo'lmadi",
        "analysis_started": "Tahlil boshlandi, iltimos keyinroq urinib ko‘ring",

        # --- Payments / Tokens ---
        "not_enough_tokens": "Sizda yetarli tokenlar yo'q.",
        "payment_not_found": "To'lov topilmadi",
        "payment_already_exists": "Bu tarif uchun to'lov allaqachon mavjud va faol",
        "payment_confirmed": "To'lov tasdiqlandi va tokenlar qo'shildi",
        "payment_failed": "To'lov amalga oshmadi",
        "test_type_not_found": "Test turi topilmadi",

        # --- Payments / New ---
        "tariff_not_found": "Tarif topilmadi",
        "payment_exists": "Faol to'lov allaqachon mavjud",
        "atm_error": "To'lov xizmati xatosi: {error}",
        "invalid_callback": "Callback ma'lumotlari noto'g'ri",
        "invalid_callback (no JSON)": "Callback ma'lumotlari noto'g'ri (JSON yo'q)",
        "tokens_for_tariff": "{tariff_name} uchun tokenlar",
        "payment_successful": "To'lov muvaffaqiyatli amalga oshirildi",
        "you_bought_tariff": "Siz {tariff_name} sotib oldingiz.",
        "tokens_credited": "{tokens} tokenlar qo'shildi.",
    },
}

async def get_translation(request: Request) -> Dict[str, str]:
    """
    Returns translation dictionary based on Accept-Language header.
    """
    raw_lang = request.headers.get("Accept-Language", "en").split(",")[0]
    lang_prefix = raw_lang.split("-")[0].lower()
    return _TRANSLATIONS.get(lang_prefix, _TRANSLATIONS["en"])
