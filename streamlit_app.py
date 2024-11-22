import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection, execute_query
import time

allowed_values = ["Nombre de boîtes délivrées", "Montant Remboursé", "Base de Remboursement"]
allowed_col_index = ["Tranche d’Age du Bénéficiaire","Sexe du Bénéficiaire", "Région de Résidence du Bénéficiaire", "Prescripteur", "Année", "Libellé ATC4", "Libellé ATC5", "Code CIP 13", "Libellé CIP 13"]

@st.cache_data(persist=True)
def fetch_atc3():
    result = execute_query(
        st_supabase_client.table("atc3_values").select("*"), ttl=0
    )
    return pd.DataFrame(result.data)


@st.cache_data(persist=True)
def fetch_data(atc3_value):
    result = execute_query(
        st_supabase_client.table("test10").select("*").ilike('Libellé ATC3', f"%{atc3_value}%")
    )
    return pd.DataFrame(result.data)   
# Function to create a dynamic pivot table
def create_pivot_table(df):
    if df is not None:
        st.sidebar.header("☕️ Filtre")
        filter_col = st.sidebar.selectbox("Créer un filtre (optionnel)", options=df.columns.tolist(), placeholder="Choisir une colonne...", index=None, key="filter_col")
        if filter_col:
            unique_vals = df[filter_col].unique().tolist()
            filter_vals = st.sidebar.multiselect("Filtrer sur... (choix multiple)", options=unique_vals, key="filter_vals")
            if filter_vals:
                df = df[df[filter_col].isin(filter_vals)]

        st.sidebar.header("🧨 Tableau croisé dynamique")
        # Select pivot fields
        index_cols = st.sidebar.multiselect("Lignes", options=allowed_col_index, default='Libellé ATC5', placeholder="Choisir une ligne...")
        column_cols = st.sidebar.multiselect("Colonnes", options=allowed_col_index, placeholder="Choisir une colonne...")
        value_col = st.sidebar.selectbox("Valeurs", options=allowed_values, key="values")
        agg_func_fr = st.sidebar.selectbox("Calcul par...", ["Moyenne","Somme", "Nombre"], key="aggregation")
        agg_func_mapping = {
            "Moyenne": "mean",
            "Somme": "sum",
            "Nombre": "count"
        }

        agg_func = agg_func_mapping.get(agg_func_fr, "mean") 
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
            st.write("### Tableau croisé dynamique")
            st.dataframe(pivot_table, use_container_width=True)
            return pivot_table, len(index_cols), len(column_cols), agg_func_fr, value_col, index_cols
        else: return None, 0, 0

# Function to visualize pivot table
def visualize_data(df, index_col_count, column_col_count , agg_func_fr, value_col, index_cols):
    if df is not None:
        st.write("### Figure")
        st.sidebar.header("📊 Graphique")
        if index_col_count <= 1 and column_col_count <= 1:
            chart_type = st.sidebar.selectbox("Select chart type", ["Bar", "Line", "Area"],  key="select chart type")

            if chart_type == "Bar":
                horizontal = st.sidebar.checkbox("Afficher le graphique horizontalement")
                stack = st.sidebar.checkbox("Stacker les sous -catégories")
                stack_100 = st.sidebar.checkbox("Stack 100%")
                if stack_100 == True:
                    stack = 'normalize'
                st.bar_chart(df, use_container_width=True,  height=600, horizontal=horizontal, stack=stack, y_label={index_cols[0]} if horizontal else {agg_func_fr + " de : " + value_col}, x_label={agg_func_fr + " de : " + value_col} if horizontal else {index_cols[0]})
            elif chart_type == "Line":
                st.line_chart(df, use_container_width=True, height=600)
            elif chart_type == "Area":
                st.area_chart(df, use_container_width=True, height=600)
        else:
            st.write("Visualization not available: Please select only one Row and one Column.")
    
# Main Streamlit App
if __name__ == "__main__":
    st.title("💊 Easy Open Medic")
    st.markdown("_Les bases open medic sont complexes à utiliser, ce site est destiné à vous faciliter la tache ;)_")
    
    st_supabase_client = st.connection(
    name="public",
    type=SupabaseConnection,
    ttl=None,
    )

    st.sidebar.header("✨")
    atc3_df = fetch_atc3()
    atc3_values = atc3_df['L_ATC3'].tolist()
    selected_atc3 = st.sidebar.selectbox("Commençons par choisir une classe ATC3 🤓", index=None ,options=atc3_values, key="selected_atc3", placeholder="selectionnez une classe ATC3...")
    
    if selected_atc3:
        st.header(selected_atc3)
        open_medic_table = fetch_data(selected_atc3)
        
        st.dataframe(open_medic_table, height=200)
        if len(open_medic_table) == 200000:
            st.write(f"Nombre de lignes : {len(open_medic_table)} - Attention, dataset incomplet, seuls les 200000 premières lignes sont prises en compte")
        else:
            st.write(f"Nombre de lignes : {len(open_medic_table)}")

        pivot_table, index_col_count, column_col_count, agg_func_fr, value_col, index_cols = create_pivot_table(open_medic_table)
        visualize_data(pivot_table, index_col_count, column_col_count, agg_func_fr , value_col, index_cols)

