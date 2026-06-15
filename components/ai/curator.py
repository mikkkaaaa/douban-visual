import streamlit as st

from components.ai.prompts import build_book_context, build_curator_system_prompt


def render_curator_chat(df_filtered, api_ready, client):
    st.info(
        f"系统会基于左侧当前筛选出的 {len(df_filtered)} 本图书进行推荐。"
        "你可以描述想读的主题、情绪状态、写作风格，或者希望控制阅读难度。"
    )

    with st.expander("AI 推荐逻辑说明"):
        st.markdown("""
        - 推荐范围只限于左侧当前筛选后的图书  
        - 回答时会优先参考书名、评分、作者信息和简介内容  
        - 如果当前书库里没有特别匹配的书，系统会直接说明，而不是编造书名  
        """)

    if df_filtered.empty:
        st.warning("当前筛选条件下没有可推荐的图书，请先调整左侧筛选条件。")
        return

    if not api_ready:
        st.error(
            "未找到 API Key 或连接失败。"
            "请确认 `.streamlit/secrets.toml` 中已经正确配置 `DEEPSEEK_API_KEY`。"
        )
        return

    st.markdown("#### 快速提问")

    q1, q2, q3 = st.columns(3)

    example_prompt = None

    with q1:
        if st.button("想读复杂人性的作品", use_container_width=True):
            example_prompt = "我想读几本关注复杂人性、道德困境和内心挣扎的书，请从当前书库中推荐。"

    with q2:
        if st.button("最近有点迷茫", use_container_width=True):
            example_prompt = "我最近有些迷茫，想读一些能帮助理解生活困境、但又不过分空泛的书，请推荐几本。"

    with q3:
        if st.button("想找俄式心理小说感", use_container_width=True):
            example_prompt = "有没有风格上接近俄国心理小说，关注罪、良心、痛苦和精神挣扎的作品？"

    message_key = "curator_messages"

    if message_key not in st.session_state:
        st.session_state[message_key] = [
            {
                "role": "assistant",
                "content": (
                    "你好，我会根据当前书库帮你挑书。"
                    "你可以直接告诉我：你最近想读什么，或者你希望从一本书里得到什么。"
                )
            }
        ]

    _, clear_col = st.columns([6, 1])
    with clear_col:
        if st.button("清空对话", use_container_width=True):
            st.session_state[message_key] = [
                {
                    "role": "assistant",
                    "content": (
                        "你好，我会根据当前书库帮你挑书。"
                        "你可以直接告诉我：你最近想读什么，或者你希望从一本书里得到什么。"
                    )
                }
            ]
            st.rerun()

    chat_container = st.container(height=500)

    with chat_container:
        for msg in st.session_state[message_key]:
            avatar = "📚" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    typed_prompt = st.chat_input(
        "例如：想读几本讨论人性与道德困境的作品；或者：有没有适合低迷时期读的书？"
    )

    user_prompt = example_prompt or typed_prompt

    if not user_prompt:
        return

    st.session_state[message_key].append(
        {
            "role": "user",
            "content": user_prompt
        }
    )

    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)

        book_context = build_book_context(df_filtered)
        system_prompt = build_curator_system_prompt(book_context)

        messages_for_api = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # 只保留最近几轮历史，避免上下文过长
        recent_history = st.session_state[message_key][-6:-1]
        messages_for_api.extend(recent_history)

        messages_for_api.append(
            {
                "role": "user",
                "content": user_prompt
            }
        )

        with st.chat_message("assistant", avatar="📚"):
            try:
                stream = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages_for_api,
                    stream=True,
                    temperature=0.7
                )

                response = st.write_stream(stream)

            except Exception as e:
                response = f"抱歉，调用 AI 服务时出现错误：{e}"
                st.error(response)

    st.session_state[message_key].append(
        {
            "role": "assistant",
            "content": response
        }
    )
