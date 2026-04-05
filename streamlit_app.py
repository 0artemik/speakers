import os

import streamlit as st
import requests

# Конфигурация страницы
st.set_page_config(page_title="Speaker Recognition", layout="wide", initial_sidebar_state="expanded")

# Стили
st.markdown(
    """
    <style>
    .success-box {
        background-color: #1e5631;
        color: #ffffff;
        padding: 20px;
        border-radius: 5px;
        border: 2px solid #40916c;
    }
    .error-box {
        background-color: #ae1e1e;
        color: #ffffff;
        padding: 20px;
        border-radius: 5px;
        border: 2px solid #ff6b6b;
    }
    .info-box {
        background-color: #1e3a5f;
        color: #ffffff;
        padding: 20px;
        border-radius: 5px;
        border: 2px solid #4a90e2;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("Speaker Recognition System")

# Конфигурация API (в Docker: API_URL=http://api:8000)
API_URL = os.getenv("API_URL", "http://localhost:8000")


def make_request(endpoint, files=None, data=None):
    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            files=files,
            data=data,
            timeout=30,
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            try:
                error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            except Exception:
                error_detail = response.text or f"HTTP {response.status_code}"
            return {"success": False, "error": error_detail}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout: сервер не ответил за 30 секунд"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": f"Не удается подключиться к API на {API_URL}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def make_get_request(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=30)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            try:
                error_detail = response.json().get("detail", f"HTTP {response.status_code}")
            except Exception:
                error_detail = response.text or f"HTTP {response.status_code}"
            return {"success": False, "error": error_detail}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout: сервер не ответил за 30 секунд"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": f"Не удается подключиться к API на {API_URL}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


if "auth" not in st.session_state:
    st.session_state["auth"] = {
        "is_authenticated": False,
        "username": None,
        "is_admin": False,
        "user_id": None,
    }


def render_auth_sidebar():
    st.sidebar.header("Авторизация")
    auth = st.session_state["auth"]

    if auth["is_authenticated"]:
        st.sidebar.success(f"Вы вошли как: {auth['username']}")
        if auth["is_admin"]:
            st.sidebar.info("Права: администратор")
        else:
            st.sidebar.info("Права: пользователь")

        if st.sidebar.button("Выйти"):
            st.session_state["auth"] = {
                "is_authenticated": False,
                "username": None,
                "is_admin": False,
                "user_id": None,
            }
            st.rerun()
        st.sidebar.markdown("---")
        return

    auth_mode = st.sidebar.radio("Режим", ["Вход", "Регистрация"])

    username = st.sidebar.text_input("Имя пользователя")
    password = st.sidebar.text_input("Пароль", type="password")

    if auth_mode == "Регистрация":
        if st.sidebar.button("Зарегистрироваться"):
            if not username or not password:
                st.sidebar.error("Введите имя пользователя и пароль")
            else:
                result = make_request(
                    "/auth/register",
                    data={"username": username, "password": password},
                )
                if result["success"]:
                    user_data = result["data"]
                    st.sidebar.success("Регистрация выполнена. Теперь войдите.")
                else:
                    st.sidebar.error(result["error"])
    else:
        if st.sidebar.button("Войти"):
            if not username or not password:
                st.sidebar.error("Введите имя пользователя и пароль")
            else:
                result = make_request(
                    "/auth/login",
                    data={"username": username, "password": password},
                )
                if result["success"]:
                    data = result["data"]
                    st.session_state["auth"] = {
                        "is_authenticated": True,
                        "username": data.get("username"),
                        "is_admin": data.get("is_admin", False),
                        "user_id": data.get("id"),
                    }
                    st.rerun()
                else:
                    st.sidebar.error(result["error"])

    st.sidebar.markdown("---")


def render_enroll_tab():
    st.header("Регистрация нового спикера")
    st.markdown("Загрузите или запишите голосовой файл для регистрации")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Загрузка файла")
        speaker_name = st.text_input("Имя спикера", placeholder="Введите имя...")
        uploaded_file = st.file_uploader(
            "Выберите аудиофайл",
            type=["wav", "mp3", "ogg"],
            key="enroll_upload",
        )

        if uploaded_file and speaker_name:
            if st.button("Регистрировать", key="enroll_btn"):
                with st.spinner("Обработка файла..."):
                    files = {"file": uploaded_file}
                    data = {"name": speaker_name}
                    result = make_request("/speakers/enroll", files=files, data=data)

                    if result["success"]:
                        response_data = result["data"]
                        st.markdown(
                            f"""
                        <div class="success-box">
                            <strong>Успешно!</strong><br>
                            Говорящий зарегистрирован:<br>
                            ID: {response_data['id']}<br>
                            Имя: {response_data['name']}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                        <div class="error-box">
                            <strong>Ошибка!</strong><br>
                            {result['error']}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

    with col2:
        st.subheader("Запись голоса")
        st.info("Убедитесь, что микрофон подключен и разрешён в браузере")
        audio_data = st.audio_input(
            "Запишите ваш голос",
            label_visibility="collapsed",
            key="enroll_audio_input",
        )

        speaker_name_right = st.text_input(
            "Имя спикера для записи",
            placeholder="Введите имя...",
            key="enroll_speaker_name_right",
        )

        if audio_data and speaker_name_right:
            if st.button("Регистрировать запись", key="enroll_record_btn"):
                with st.spinner("Обработка записи..."):
                    files = {"file": ("recording.wav", audio_data)}
                    data = {"name": speaker_name_right}
                    result = make_request("/speakers/enroll", files=files, data=data)

                    if result["success"]:
                        response_data = result["data"]
                        st.markdown(
                            f"""
                        <div class="success-box">
                            <strong>Успешно!</strong><br>
                            Спикер зарегистрирован:<br>
                            ID: {response_data['id']}<br>
                            Имя: {response_data['name']}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                        <div class="error-box">
                            <strong>Ошибка!</strong><br>
                            {result['error']}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )


def render_identify_tab():
    st.header("Идентификация спикера")
    st.markdown("Загрузите или запишите голос для определения, кто говорит")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Загрузка файла")
        identify_file = st.file_uploader(
            "Выберите аудиофайл",
            type=["wav", "mp3", "ogg"],
            key="identify_upload",
        )

        if identify_file:
            st.audio(identify_file)
            if st.button("Идентифицировать", key="identify_btn"):
                with st.spinner("Анализ голоса..."):
                    files = {"file": identify_file}
                    result = make_request("/speakers/identify", files=files)

                    if result["success"]:
                        response_data = result["data"]
                        match = response_data.get("match")
                        score = response_data.get("score", 0)

                        if match:
                            st.markdown(
                                f"""
                            <div class="success-box">
                                <strong>Совпадение найдено!</strong><br>
                                Спикер: <b>{match}</b><br>
                                схожесть: {score:.2%}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                            st.progress(min(score, 1.0))
                        else:
                            st.markdown(
                                f"""
                            <div class="info-box">
                                <strong>ℹСовпадение не найдено</strong><br>
                                Максимальная схожесть: {score:.2%}<br>
                                (минимальный порог: 65%)
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            f"""
                        <div class="error-box">
                            <strong>Ошибка!</strong><br>
                            {result['error']}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

    with col2:
        st.subheader("Запись голоса")
        st.info("Убедитесь, что микрофон подключен и разрешён в браузере")
        identify_audio = st.audio_input(
            "Запишите ваш голос",
            label_visibility="collapsed",
            key="identify_audio_input",
        )

        if identify_audio:
            if st.button("Идентифицировать запись", key="identify_record_btn"):
                with st.spinner("Анализ записи..."):
                    files = {"file": ("recording.wav", identify_audio)}
                    result = make_request("/speakers/identify", files=files)

                    if result["success"]:
                        response_data = result["data"]
                        match = response_data.get("match")
                        score = response_data.get("score", 0)

                        if match:
                            st.markdown(
                                f"""
                            <div class="success-box">
                                <strong>Совпадение найдено!</strong><br>
                                Спикер: <b>{match}</b><br>
                                схожесть: {score:.2%}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                            st.progress(min(score, 1.0))
                        else:
                            st.markdown(
                                f"""
                            <div class="info-box">
                                <strong>ℹСовпадение не найдено</strong><br>
                                Максимальная схожесть: {score:.2%}<br>
                                (минимальный порог: 65%)
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            f"""
                        <div class="error-box">
                            <strong>Ошибка!</strong><br>
                            {result['error']}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )


def render_admin_tab():
    st.header("Администрирование: спикеры и эмбеддинги")
    st.markdown("Список всех зарегистрированных спикеров и их эмбеддингов.")

    result = make_get_request("/speakers")
    if not result["success"]:
        st.markdown(
            f"""
        <div class="error-box">
            <strong>Ошибка!</strong><br>
            {result['error']}
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    speakers = result["data"]
    if not speakers:
        st.info("Пока нет зарегистрированных спикеров.")
        return

    for sp in speakers:
        st.markdown(f"**ID:** {sp['id']} &nbsp;&nbsp; **Имя:** {sp['name']} &nbsp;&nbsp; **Дата:** {sp['created_at']}")
        embedding_preview = sp.get("embedding") or []
        if embedding_preview:
            emb_str = ", ".join(f"{v:.4f}" for v in embedding_preview[:10])
            if len(embedding_preview) > 10:
                emb_str += ", ..."
            st.code(emb_str)
        st.markdown("---")


render_auth_sidebar()

auth_state = st.session_state["auth"]

if not auth_state["is_authenticated"]:
    st.warning("Для работы с системой необходимо войти или зарегистрироваться через боковую панель.")
else:
    tabs = ["Регистрация (Enroll)", "Идентификация (Identify)"]
    if auth_state["is_admin"]:
        tabs.append("Админ: спикеры")

    tab_objects = st.tabs(tabs)

    if "Регистрация (Enroll)" in tabs:
        with tab_objects[tabs.index("Регистрация (Enroll)")]:
            render_enroll_tab()

    if "Идентификация (Identify)" in tabs:
        with tab_objects[tabs.index("Идентификация (Identify)")]:
            render_identify_tab()

    if "Админ: спикеры" in tabs and auth_state["is_admin"]:
        with tab_objects[tabs.index("Админ: спикеры")]:
            render_admin_tab()



