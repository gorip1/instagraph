import streamlit as st
import pandas as pd

# Function to upload multiple files
def upload_multiple_files():
    uploaded_files = st.sidebar.file_uploader("Choose CSV files", type="csv", accept_multiple_files=True)
    tables = {}
    for uploaded_file in uploaded_files:
        tables[uploaded_file.name] = pd.read_csv(uploaded_file, sep=";")
    return tables

# Function to create a dynamic pivot table
def create_pivot_table(df):
    if df is not None:
        st.sidebar.header("Dynamic Pivot Table")
        # Select pivot columns
        index_cols = st.sidebar.multiselect("Index", options=df.columns)
        value_col = st.sidebar.selectbox("Values", options=df.columns)
        agg_func = st.sidebar.selectbox("Aggregation", ["sum", "mean", "count"])
        
        if index_cols and value_col:
            pivot_table = df.pivot_table(index=index_cols, values=value_col, aggfunc=agg_func)
            st.write(pivot_table)
            return pivot_table

# Function to visualize pivot table
def visualize_data(df):
    if df is not None:
        st.sidebar.header("Visualization")
        chart_type = st.sidebar.selectbox("Select chart type", ["Bar", "Line", "Heatmap"])

        fig, ax = plt.subplots()
        if chart_type == "Bar":
            df.plot.bar(ax=ax)
        elif chart_type == "Line":
            df.plot.line(ax=ax)
        elif chart_type == "Heatmap":
            sns.heatmap(df, annot=True, fmt=".1f", cmap="coolwarm", ax=ax)
        
        st.pyplot(fig)

# Main Streamlit App
if __name__ == "__main__":
    st.title("Interactive Data Exploration App")

    tables = upload_multiple_files()

    if tables:
        table_choice = st.sidebar.selectbox("Select a table", options=tables.keys())

        if table_choice:
            current_df = tables[table_choice]
            st.write(f"Data from {table_choice}")
            st.dataframe(current_df)

            pivot_table = create_pivot_table(current_df)
            visualize_data(pivot_table)
