import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection, execute_query
import time

@st.cache_data(ttl=600, persist=True)
def fetch_data(search_column, search_query):
    if search_query:
        result = execute_query(
            st_supabase_client.table("OPEN_MEDIC").select("*").ilike(search_column, f"%{search_query}%"), ttl=0
        )
    else:
        result = execute_query(st_supabase_client.table("OPEN_MEDIC").select("*"), ttl=600)
    
    return pd.DataFrame(result.data)  
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
        value_col = st.sidebar.selectbox("Values", options=df.columns, index=21, key="values")
        agg_func = st.sidebar.selectbox("Aggregation", ["mean","sum", "count"], key="aggregation")

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
            st.write(len(column_cols))
            st.dataframe(pivot_table, use_container_width=True)
            return pivot_table, len(index_cols), len(column_cols)
        else: return None, 0, 0

# Function to visualize pivot table
def visualize_data(df, index_col_count, column_col_count):
    if df is not None:
        st.sidebar.header("Visualization")
        if index_col_count <= 1 and column_col_count <= 1:
            chart_type = st.sidebar.selectbox("Select chart type", ["Bar", "Line", "Area"],  key="select chart type")

            if chart_type == "Bar":
                horizontal = st.checkbox("Afficher le graphique horizontalement")
                stack = st.checkbox("Stacker les sous -catégories")
                stack_100 = st.checkbox("Stack 100%")
                if stack_100 == True:
                    stack = 'normalize'
                st.bar_chart(df, use_container_width=True,  height=600, horizontal=horizontal, stack=stack)
            elif chart_type == "Line":
                st.line_chart(df, use_container_width=True, height=600)
            elif chart_type == "Area":
                st.area_chart(df, use_container_width=True, height=600)
        else:
            st.write("Visualization not available: Please select only one Row and one Column.")
    
# Main Streamlit App
if __name__ == "__main__":
    st.title("💊 Instagraph")
    
    st_supabase_client = st.connection(
    name="public",
    type=SupabaseConnection,
    ttl=None,
    )

    st.sidebar.header("Choisissez une classe ATC3")
    atc3_query = execute_query(
        st_supabase_client.table("atc3_values").select("*"), ttl=0
    )
    atc3_df = pd.DataFrame(atc3_query.data)
    atc3_values = atc3_df['L_ATC3'].tolist()
    selected_atc3 = st.sidebar.selectbox("Select ATC3", index=None ,options=atc3_values, key="selected_atc3")
    
    if selected_atc3:
        st.header(selected_atc3)
        query = fetch_data('L_ATC3', selected_atc3)
        open_medic_table = pd.DataFrame(query)
        
        st.dataframe(open_medic_table)
        st.write("Nombre de lignes :", len(open_medic_table))

        pivot_table, index_col_count, column_col_count = create_pivot_table(open_medic_table)
        visualize_data(pivot_table, index_col_count, column_col_count)

