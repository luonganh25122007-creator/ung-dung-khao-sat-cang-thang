"""Ứng dụng khảo sát và phân tích mức độ căng thẳng của học sinh."""

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except ModuleNotFoundError:
    px = None


# Cấu hình chung và nơi lưu dữ liệu khảo sát
APP_TITLE = "Ứng dụng Khảo sát và Phân tích Mức độ Căng thẳng của Học sinh"
DATA_FILE = Path(__file__).resolve().with_name("stress_data.csv")

QUESTIONS = {
    "bai_tap": ("Áp lực bài tập", "Tôi thường cảm thấy quá tải vì bài tập và hạn nộp."),
    "diem_so": ("Lo âu điểm số", "Tôi lo lắng nhiều về điểm số hoặc kết quả học tập."),
    "giac_ngu": ("Giấc ngủ", "Tôi khó ngủ hoặc ngủ không đủ vì việc học hay lo lắng."),
    "thoi_gian": ("Quản lý thời gian", "Tôi khó sắp xếp thời gian giữa học tập và nghỉ ngơi."),
    "ban_be": ("Quan hệ bạn bè", "Mối quan hệ với bạn bè khiến tôi căng thẳng."),
    "thay_co": ("Quan hệ thầy cô", "Tôi thấy áp lực hoặc khó trao đổi với thầy cô."),
    "suc_khoe": ("Sức khỏe và tinh thần", "Gần đây tôi thường mệt mỏi, bồn chồn hoặc khó tập trung."),
}
CSV_COLUMNS = [
    "student",
    "class_name",
    "submitted_at",
    *QUESTIONS.keys(),
    "total_score",
    "stress_level",
]
LIKERT_LABELS = {
    1: "1 - Không bao giờ",
    2: "2 - Hiếm khi",
    3: "3 - Thỉnh thoảng",
    4: "4 - Thường xuyên",
    5: "5 - Gần như luôn luôn",
}

st.set_page_config(page_title=APP_TITLE, page_icon="🌿", layout="wide")


# Phân loại điểm khảo sát; đây là công cụ tự đánh giá, không phải chẩn đoán.
def classify_score(score):
    if score <= 14:
        return "Thấp"
    if score <= 21:
        return "Trung bình"
    if score <= 28:
        return "Cao"
    return "Báo động"


# Đọc dữ liệu và kiểm tra tệp CSV để không ghi nối vào dữ liệu sai cấu trúc.
def load_data():
    try:
        if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
            return pd.DataFrame(columns=CSV_COLUMNS), None
        data = pd.read_csv(DATA_FILE)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
        return pd.DataFrame(columns=CSV_COLUMNS), f"Không thể đọc tệp dữ liệu: {error}"

    if list(data.columns) != CSV_COLUMNS:
        return (
            pd.DataFrame(columns=CSV_COLUMNS),
            "Cấu trúc stress_data.csv không đúng với ứng dụng. "
            "Vui lòng sao lưu và kiểm tra tệp trước khi tiếp tục.",
        )

    data["total_score"] = pd.to_numeric(data["total_score"], errors="coerce")
    if data["total_score"].isna().any():
        return pd.DataFrame(columns=CSV_COLUMNS), "Tệp dữ liệu có điểm số không hợp lệ."
    return data, None


# Lưu câu trả lời vào CSV; báo lỗi rõ ràng nếu không thể ghi tệp.
def append_response(response):
    _, error = load_data()
    if error:
        return error

    try:
        write_header = not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0
        pd.DataFrame([response], columns=CSV_COLUMNS).to_csv(
            DATA_FILE,
            mode="a",
            header=write_header,
            index=False,
            encoding="utf-8",
        )
    except OSError as write_error:
        return f"Không thể lưu kết quả vào {DATA_FILE.name}: {write_error}"
    return None


# Nội dung gợi ý được điều chỉnh theo mức điểm, không thay thế tư vấn chuyên môn.
def recommendations_for(level):
    recommendations = {
        "Thấp": [
            "Duy trì thời gian biểu cân bằng, xen kẽ học tập với vận động và nghỉ ngơi.",
            "Thử Pomodoro: tập trung 25 phút, nghỉ ngắn 5 phút sau mỗi phiên.",
            "Tiếp tục chia sẻ với người thân hoặc thầy cô khi có điều khiến bạn bận tâm.",
        ],
        "Trung bình": [
            "Ghi ra các việc cần làm, chọn 2–3 việc quan trọng nhất trong ngày và chia nhỏ từng bước.",
            "Thử Pomodoro 25/5; sau 4 phiên, nghỉ dài hơn và tránh ôm nhiều việc cùng lúc.",
            "Thư giãn bằng cách hít vào chậm 4 nhịp, thở ra 6 nhịp trong vài phút; dừng lại nếu thấy khó chịu.",
            "Trao đổi với bạn tin cậy, giáo viên chủ nhiệm hoặc người thân để cùng tìm cách giảm áp lực.",
        ],
        "Cao": [
            "Tạm chia bài vở thành các bước nhỏ, ưu tiên việc gần hạn và xin hỗ trợ điều chỉnh kế hoạch khi cần.",
            "Sắp xếp thời gian nghỉ và ngủ đều đặn; hạn chế học liên tục trong thời gian dài.",
            "Thử thở chậm hoặc thư giãn cơ nhẹ nhàng; chọn cách phù hợp và dừng nếu thấy không thoải mái.",
            "Nên sớm nói chuyện với người lớn đáng tin cậy, giáo viên tư vấn hoặc chuyên viên tâm lý học đường.",
        ],
        "Báo động": [
            "Hãy chia sẻ kết quả này sớm với cha mẹ/người giám hộ, giáo viên tư vấn hoặc chuyên viên tâm lý.",
            "Nhờ người tin cậy cùng bạn sắp xếp lại áp lực học tập và tìm hỗ trợ phù hợp; bạn không cần tự xoay xở một mình.",
            "Nếu bạn cảm thấy không an toàn hoặc có nguy cơ làm hại bản thân, hãy báo ngay cho người lớn đáng tin cậy ở gần và liên hệ dịch vụ khẩn cấp tại địa phương.",
        ],
    }
    return recommendations[level]


# Tiêu đề và thông tin lưu ý về quyền riêng tư.
st.title(APP_TITLE)
st.caption(
    "Khảo sát tự đánh giá nhằm giúp học sinh nhận diện áp lực và tìm hỗ trợ phù hợp. "
    "Kết quả không phải chẩn đoán y khoa."
)

home_tab, survey_tab, results_tab, admin_tab = st.tabs(
    ["🏠 Giới thiệu", "📝 Khảo sát", "📊 Kết quả & Đề xuất", "📋 Dữ liệu quản lý"]
)


# Trang chủ giới thiệu mục đích và phạm vi sử dụng.
with home_tab:
    st.header("Chăm sóc sức khỏe tinh thần trong học tập")
    st.write(
        "Ứng dụng giúp học sinh nhìn lại những áp lực thường gặp như bài tập, "
        "điểm số, giấc ngủ và các mối quan hệ. Từ đó, các em có thể lựa chọn "
        "một vài cách chăm sóc bản thân và chủ động tìm người hỗ trợ."
    )
    st.info(
        "Khảo sát mang tính tham khảo, không dùng để chẩn đoán hay thay thế "
        "trao đổi với chuyên gia. Nếu đang gặp khó khăn, hãy chia sẻ với người "
        "lớn mà bạn tin tưởng hoặc bộ phận tư vấn học đường."
    )
    st.markdown(
        """
        **Cách sử dụng**
        1. Mở tab **Khảo sát**, nhập thông tin và chọn mức độ phù hợp cho từng câu.
        2. Gửi khảo sát để xem tổng điểm, biểu đồ và gợi ý trong tab **Kết quả & Đề xuất**.
        3. Tab **Dữ liệu quản lý** hiển thị thống kê tổng hợp; câu trả lời được lưu
           trong `stress_data.csv` cạnh tệp ứng dụng.
        """
    )
    st.caption(
        "Chỉ nhập thông tin cần thiết. Dữ liệu được lưu cục bộ; không triển khai "
        "ứng dụng công khai nếu chưa có biện pháp bảo vệ và phân quyền phù hợp."
    )


# Biểu mẫu khảo sát với xác thực thông tin, xác nhận đồng ý và đủ câu trả lời.
with survey_tab:
    st.header("Khảo sát mức độ căng thẳng")
    st.write(
        "Chọn một mức cho mỗi câu: 1 là không bao giờ, 5 là gần như luôn luôn. "
        "Hãy trả lời theo trải nghiệm gần đây của bạn."
    )
    with st.form("stress_survey_form"):
        student = st.text_input("Họ tên hoặc mã số học sinh", max_chars=100)
        class_name = st.text_input("Lớp", max_chars=50)

        answers = {}
        for key, (aspect, question) in QUESTIONS.items():
            answers[key] = st.radio(
                f"**{aspect}:** {question}",
                options=list(LIKERT_LABELS),
                index=None,
                format_func=lambda value: LIKERT_LABELS[value],
                horizontal=True,
                key=f"answer_{key}",
            )

        consent = st.checkbox(
            "Tôi hiểu đây là khảo sát tham khảo và đồng ý lưu câu trả lời "
            "trong tệp CSV của ứng dụng để thống kê.",
            key="survey_consent",
        )
        submitted = st.form_submit_button("Gửi kết quả và Phân tích", type="primary")

    if submitted:
        if not student.strip() or not class_name.strip():
            st.error("Vui lòng nhập họ tên hoặc mã số học sinh và lớp.")
        elif any(value is None for value in answers.values()):
            st.error("Vui lòng trả lời đầy đủ cả 7 câu hỏi.")
        elif not consent:
            st.error("Vui lòng xác nhận đã hiểu và đồng ý với việc lưu dữ liệu.")
        else:
            total_score = sum(answers.values())
            level = classify_score(total_score)
            response = {
                "student": student.strip(),
                "class_name": class_name.strip(),
                "submitted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                **answers,
                "total_score": total_score,
                "stress_level": level,
            }
            save_error = append_response(response)
            if save_error:
                st.error(save_error)
            else:
                st.session_state["latest_result"] = response
                st.success(
                    "Đã lưu khảo sát. Chuyển sang tab **Kết quả & Đề xuất** "
                    "để xem phân tích của bạn."
                )


# Trình bày kết quả lần khảo sát gần nhất trong phiên hiện tại.
with results_tab:
    st.header("Kết quả & Đề xuất")
    latest = st.session_state.get("latest_result")
    if latest is None:
        st.info("Bạn hãy hoàn thành và gửi khảo sát để xem kết quả tại đây.")
    else:
        score = int(latest["total_score"])
        level = latest["stress_level"]
        first_metric, second_metric = st.columns(2)
        first_metric.metric("Tổng điểm", f"{score} / 35")
        second_metric.metric("Mức độ tham khảo", level)

        if level == "Thấp":
            st.success("Mức điểm hiện tại nằm trong khoảng thấp.")
        elif level == "Trung bình":
            st.info("Một số áp lực có thể đang ảnh hưởng đến bạn; hãy thử các gợi ý dưới đây.")
        else:
            st.warning(
                "Điểm khảo sát cao không phải chẩn đoán. Hãy cân nhắc chia sẻ với "
                "người lớn đáng tin cậy hoặc bộ phận tư vấn học đường."
            )

        chart_data = pd.DataFrame(
            {
                "Khía cạnh": [QUESTIONS[key][0] for key in QUESTIONS],
                "Điểm (1–5)": [latest[key] for key in QUESTIONS],
            }
        )
        if px is not None:
            figure = px.bar(
                chart_data,
                x="Khía cạnh",
                y="Điểm (1–5)",
                color="Điểm (1–5)",
                color_continuous_scale=["#8bcf9b", "#f5c45e", "#d95d5d"],
                range_color=(1, 5),
                range_y=(0, 5),
                title="Các khía cạnh được tự đánh giá",
            )
            figure.update_layout(
                coloraxis_showscale=False,
                xaxis_title="",
                yaxis_title="Mức độ (1–5)",
                margin=dict(t=55, b=20),
            )
            st.plotly_chart(figure, width="stretch")
        else:
            st.bar_chart(chart_data, x="Khía cạnh", y="Điểm (1–5)")
        st.markdown("#### Gợi ý phù hợp")
        for suggestion in recommendations_for(level):
            st.markdown(f"- {suggestion}")
        st.caption(
            "Điểm càng cao thể hiện trải nghiệm căng thẳng được báo cáo càng thường xuyên. "
            "Hãy chọn lời khuyên khiến bạn thấy phù hợp; bạn có thể bỏ qua nếu không thoải mái."
        )


# Dashboard chỉ hiển thị số liệu tổng hợp, không đưa danh sách tên/mã học sinh lên giao diện.
with admin_tab:
    st.header("Thống kê tổng hợp")
    data, data_error = load_data()
    if data_error:
        st.error(data_error)
    elif data.empty:
        st.info("Chưa có dữ liệu khảo sát. Sau khi gửi khảo sát, thống kê sẽ xuất hiện tại đây.")
    else:
        total_students = len(data)
        overall_average = data["total_score"].mean()
        metric_count, metric_average = st.columns(2)
        metric_count.metric("Số lượt khảo sát", total_students)
        metric_average.metric("Điểm trung bình chung", f"{overall_average:.1f} / 35")

        st.subheader("Phân bố mức độ tham khảo")
        level_order = ["Thấp", "Trung bình", "Cao", "Báo động"]
        level_counts = (
            data["stress_level"]
            .value_counts()
            .reindex(level_order, fill_value=0)
            .rename_axis("Mức độ")
            .reset_index(name="Số lượt")
        )
        st.bar_chart(level_counts, x="Mức độ", y="Số lượt", width="stretch")

        st.subheader("Thống kê theo lớp")
        class_summary = (
            data.groupby("class_name", as_index=False)
            .agg(
                so_luot=("total_score", "size"),
                diem_trung_binh=("total_score", "mean"),
            )
        )
        class_summary = class_summary[class_summary["so_luot"] >= 3].copy()
        if class_summary.empty:
            st.info("Chưa hiển thị thống kê lớp: cần ít nhất 3 lượt khảo sát trong mỗi lớp.")
        else:
            class_summary["diem_trung_binh"] = class_summary["diem_trung_binh"].round(1)
            class_summary = class_summary.rename(
                columns={
                    "class_name": "Lớp",
                    "so_luot": "Số lượt khảo sát",
                    "diem_trung_binh": "Điểm trung bình",
                }
            )
            st.dataframe(class_summary, hide_index=True, width="stretch")
            st.caption("Lớp có dưới 3 lượt khảo sát được ẩn để hạn chế nhận diện cá nhân.")

        st.caption(
            "Tệp CSV chứa thông tin người trả lời và câu trả lời chi tiết. "
            "Không chia sẻ tệp này hoặc triển khai dashboard công khai khi chưa được phép."
        )
