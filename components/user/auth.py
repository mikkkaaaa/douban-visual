import streamlit as st

from lib.user_database import init_user_tables, create_user, login_user


def init_auth_state():
    if "user" not in st.session_state:
        st.session_state.user = None


def is_logged_in():
    init_auth_state()
    return st.session_state.get("user") is not None


def get_current_user():
    init_auth_state()
    return st.session_state.get("user")


def logout_user():
    st.session_state.user = None
    st.rerun()


def render_auth_sidebar_entry():
    """
    左上角轻量用户入口。
    不强制登录，游客也可以使用公共功能。
    """
    init_user_tables()
    init_auth_state()

    with st.sidebar:
        st.markdown("### 用户入口")

        if is_logged_in():
            user = get_current_user()
            username = user.get("username", "User")
            avatar_text = username[0].upper() if username else "U"

            st.markdown(
                f"""
                <div class="user-mini-card">
                    <div class="user-avatar">{avatar_text}</div>
                    <div>
                        <div class="user-name">{username}</div>
                        <div class="user-role">已登录，可使用个人书库</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("退出登录", use_container_width=True):
                logout_user()

            st.divider()
            return

        st.markdown(
            """
            <div class="guest-mini-card">
                <div class="guest-title">游客模式</div>
                <div class="guest-desc">可浏览公共书库、数据可视化和 AI 推荐。登录后可使用个人书库。</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("登录 / 注册", expanded=False):
            login_tab, register_tab = st.tabs(["登录", "注册"])

            with login_tab:
                with st.form("sidebar_login_form", clear_on_submit=False):
                    username = st.text_input(
                        "用户名",
                        key="sidebar_login_username",
                        placeholder="请输入用户名"
                    )

                    password = st.text_input(
                        "密码",
                        type="password",
                        key="sidebar_login_password",
                        placeholder="请输入密码"
                    )

                    submitted = st.form_submit_button(
                        "登录",
                        use_container_width=True
                    )

                    if submitted:
                        ok, result = login_user(username, password)

                        if ok:
                            st.session_state.user = result
                            st.success("登录成功")
                            st.rerun()
                        else:
                            st.error(result)

            with register_tab:
                with st.form("sidebar_register_form", clear_on_submit=False):
                    new_username = st.text_input(
                        "用户名",
                        key="sidebar_register_username",
                        placeholder="至少 3 个字符"
                    )

                    new_password = st.text_input(
                        "密码",
                        type="password",
                        key="sidebar_register_password",
                        placeholder="至少 6 位"
                    )

                    confirm_password = st.text_input(
                        "确认密码",
                        type="password",
                        key="sidebar_register_confirm_password",
                        placeholder="再次输入密码"
                    )

                    submitted = st.form_submit_button(
                        "创建账号",
                        use_container_width=True
                    )

                    if submitted:
                        if not new_username.strip():
                            st.error("用户名不能为空")
                        elif len(new_username.strip()) < 3:
                            st.error("用户名至少需要 3 个字符")
                        elif len(new_password) < 6:
                            st.error("密码至少需要 6 位")
                        elif new_password != confirm_password:
                            st.error("两次输入的密码不一致")
                        else:
                            ok, message = create_user(new_username, new_password)

                            if ok:
                                st.success("注册成功，请切换到登录页登录")
                            else:
                                st.error(message)

        st.divider()


def render_login_required_card(feature_name="个人书库"):
    """
    某些功能需要登录时，在页面中显示提示卡片。
    """
    st.markdown(
        f"""
        <div class="login-required-card">
            <h3>{feature_name}需要登录后使用</h3>
            <p>
            公共书库、数据可视化和 AI 推荐功能可以直接使用。
            登录后，你可以上传自己的书籍数据，建立个人书库，并让 AI 分析你的阅读数据。
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
