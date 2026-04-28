import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Cylinder Schedule Generator", layout="wide")
st.title("🔐 Door Cylinder Schedule Generator")
st.markdown("Upload a manufacturing schedule (Excel or CSV) to automatically create a cylinder schedule based on **Door Pack**.")

def get_cylinder_type(door_pack):
    try:
        pack = int(door_pack)
    except (ValueError, TypeError):
        return "Unknown – check manually"
    if pack == 1:
        return "70mm double euro"
    elif pack in [2, 3, 4, 5, 6]:
        return "45mm single half euro"
    else:
        return f"Unknown – pack {pack}"

uploaded_file = st.file_uploader("Upload Manufacturing Schedule", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    st.subheader("Preview of uploaded data (first 10 rows)")
    st.dataframe(df.head(10))

    # Auto-detect columns
    col_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if "door name" in col_lower or "room description" in col_lower:
            col_mapping["door_name"] = col
        elif "door number" in col_lower or "door ref" in col_lower:
            col_mapping["door_number"] = col
        elif "door pack" in col_lower:
            col_mapping["door_pack"] = col

    if not col_mapping.get("door_pack"):
        st.error("❌ Could not find a 'Door Pack' column.")
        st.stop()

    with st.expander("🔧 Column mapping (adjust if wrong)"):
        door_name_col = st.selectbox("Door Name / Room Description column", df.columns, index=df.columns.get_loc(col_mapping.get("door_name", df.columns[0])) if col_mapping.get("door_name") else 0)
        door_number_col = st.selectbox("Door Number column", df.columns, index=df.columns.get_loc(col_mapping.get("door_number", df.columns[1])) if col_mapping.get("door_number") else 1)
        door_pack_col = st.selectbox("Door Pack column", df.columns, index=df.columns.get_loc(col_mapping["door_pack"]))

    df["CYLINDER REQUIRED"] = df[door_pack_col].apply(get_cylinder_type)

    cylinder_schedule = df[[door_name_col, door_number_col, door_pack_col, "CYLINDER REQUIRED"]].copy()
    cylinder_schedule.columns = ["DOOR NAME", "DOOR NUMBER", "DOOR PACK", "CYLINDER REQUIRED"]

    cylinder_types = ["40mm single half euro", "45mm single half euro", "60mm double euro", "70mm double euro"]
    totals = {cyl: (cylinder_schedule["CYLINDER REQUIRED"] == cyl).sum() for cyl in cylinder_types}

    st.subheader("📊 Cylinder Schedule (Doors)")
    st.dataframe(cylinder_schedule, use_container_width=True)

    st.subheader("📈 Summary Totals")
    summary_df = pd.DataFrame({"CYLINDER TYPE": list(totals.keys()), "TOTAL CYLINDERS REQUIRED": list(totals.values())})
    st.dataframe(summary_df, use_container_width=True)

    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        cylinder_schedule.to_excel(writer, sheet_name="Cylinder Schedule", index=False)
        summary_df.to_excel(writer, sheet_name="Totals", index=False)
    output_excel.seek(0)

    st.download_button(label="📥 Download Cylinder Schedule (Excel)", data=output_excel, file_name="cylinder_schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
