import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection, execute_query
import time



# Function to create a dynamic pivot table
def create_pivot_table(df):
    if df is not None:
        st.sidebar.header("Dynamic Pivot Table")

        filter_col = st.sidebar.selectbox("Filter Column", options=["None"] + df.columns.tolist(), key="filter_col")
        if filter_col != "None":
            unique_vals = df[filter_col].unique().tolist()
            filter_vals = st.sidebar.multiselect("Filter Values", options=unique_vals, key="filter_vals")
            if filter_vals:
                df = df[df[filter_col].isin(filter_vals)]
        
        # Select pivot fields
        index_cols = st.sidebar.multiselect("Rows", options=df.columns)
        column_cols = st.sidebar.multiselect("Columns", options=df.columns)
        value_col = st.sidebar.selectbox("Values", options=df.columns, key="values")
        agg_func = st.sidebar.selectbox("Aggregation", ["sum", "mean", "count"], key="aggregation")

        # Ensure we have valid selections
        if index_cols and value_col:
            pivot_table = df.pivot_table(
                index=index_cols,
                columns=column_cols if column_cols else None,
                values=value_col,
                aggfunc=agg_func,
                fill_value=0  # Fill NaNs with zero for the purpose of the pivot view
            )
            
            # Render the pivot table in Streamlit
            st.write("### Pivot Table")
            st.dataframe(pivot_table, use_container_width=True)
            return pivot_table

# Function to visualize pivot table
def visualize_data(df):
    if df is not None:
        st.sidebar.header("Visualization")
        chart_type = st.sidebar.selectbox("Select chart type", ["Bar", "Line", "Area"],  key="select chart type")

        if chart_type == "Bar":
            horizontal = st.checkbox("Afficher le graphique horizontalement")
            stack = st.checkbox("Stacker les sous -catégories")
            st.bar_chart(df, use_container_width=True,  height=600, horizontal=horizontal, stack=stack)
        elif chart_type == "Line":
            st.line_chart(df, use_container_width=True, height=600)
        elif chart_type == "Area":
            st.area_chart(df, use_container_width=True, height=600)

        
# Main Streamlit App
if __name__ == "__main__":
    st.title("Instagraph")
    
    st_supabase_client = st.connection(
    name="public",
    type=SupabaseConnection,
    ttl=None,
    )

    query = execute_query(st_supabase_client.table("OPEN_MEDIC").select("*"), ttl=0)
    open_medic_table = pd.DataFrame(query.data)
    st.write(len(open_medic_table))
    st.sidebar.header("Search Filter")
    search_column = st.sidebar.selectbox("Select column to search", options=open_medic_table.columns, key="search_column")
    search_query = st.sidebar.text_input("Enter your search query", key="search_query")

    # Filter the main DataFrame based on search input
    if search_query:
        open_medic_table = open_medic_table[open_medic_table[search_column].astype(str).str.contains(search_query, case=False, na=False)]

    st.dataframe(open_medic_table)
    pivot_table = create_pivot_table(open_medic_table)
    visualize_data(pivot_table)

