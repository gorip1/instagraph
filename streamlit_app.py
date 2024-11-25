import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection, execute_query
import altair as alt

allowed_values = ["Montant Remboursé", "Nombre de boîtes délivrées", "Base de Remboursement"]
allowed_col_index = ["Tranche d’Age du Bénéficiaire","Sexe du Bénéficiaire", "Région de Résidence du Bénéficiaire", "Prescripteur", "Année", "Libellé ATC4", "Libellé ATC5", "Code CIP 13", "Libellé CIP 13"]
all_years = [2021, 2022, 2023]
selected_atc3 = None
selected_atc3_label = None
### GET DB FUNCTIONS


@st.cache_data(persist=True)
def fetch_atc3():
    result = execute_query(
        st_supabase_client.table("atc3_code_and_labels").select("*"), ttl=0
    )
    return pd.DataFrame(result.data)

@st.cache_data(persist=True)
def fetch_atc5():
    result = execute_query(
        st_supabase_client.table("atc5_code_and_labels").select("*"), ttl=0
    )
    return pd.DataFrame(result.data)

@st.cache_data(persist=True)
def fetch_drug_atc3(atc5):
    result = execute_query(
        st_supabase_client.table("test12")
        .select("Code ATC3", "Libellé ATC3")
        .eq("Code ATC5", atc5)
        .limit(1)
    )
    return pd.DataFrame(result.data)

@st.cache_data(persist=True)
def fetch_data(column, value):
    result = execute_query(
        st_supabase_client.table("test12").select("*").ilike(column, f"%{value}%")
    )
    return pd.DataFrame(result.data)   


# Function to create a dynamic pivot table

def create_pivot_table(df):
    if df is not None:
        st.sidebar.header("☕️ Filtres")

        selected_years = st.sidebar.multiselect(
            "Sélectionner les années",
            options=list(all_years),
            default=all_years)
        
        df = df[df["Année"].isin(selected_years)]

        def apply_filter(filter_index):
            filter_col = st.sidebar.selectbox(f"Filtre {filter_index}", options=df.columns.tolist(), placeholder="Choisir une colonne...", key=f"filter_col_{filter_index}", index=None)
            if filter_col:
                unique_vals = df[filter_col].unique().tolist()
                filter_vals = st.sidebar.multiselect("  ____👉 Filtrer sur... (choix multiple)", options=unique_vals, key=f"filter_vals_{filter_index}")
                return (filter_col, filter_vals)
            return (None, None)

        for i in range(1, 4):
            filter_col, filter_vals = apply_filter(i)
            if filter_col and filter_vals:
                df = df[df[filter_col].isin(filter_vals)]

        st.sidebar.header("🧨 Tableau croisé dynamique")
        # Select pivot fields
        index_cols = st.sidebar.multiselect("Lignes", options=allowed_col_index, default='Libellé ATC5', placeholder="Choisir une ligne...")
        column_cols = st.sidebar.multiselect("Colonnes (sous-catégorie)", options=allowed_col_index, placeholder="Choisir une colonne...", default="Année")
        value_col = st.sidebar.selectbox("Valeurs", options=allowed_values, key="values")
        agg_func_fr = st.sidebar.selectbox("Calcul par...", ["Somme"], key="aggregation")
        agg_func_mapping = {
            "Somme": "sum",
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
            st.subheader(":blue[Tableau croisé dynamique:]")
            st.dataframe(pivot_table, use_container_width=True)
            return pivot_table, len(index_cols), len(column_cols), agg_func_fr, value_col, index_cols
        else: return None, 0, 0, None, 0, 0


# Function to visualize pivot table

def visualize_data(df, index_col_count, column_col_count , agg_func_fr, value_col, index_cols):
    if df is not None:
        st.divider()
        st.subheader(":blue[Figure:]")
        if index_col_count <= 1 and column_col_count <= 1:
            chart_type = st.selectbox("Selectionner le type de graphique...", ["Bar", "Line", "Area"],  key="select chart type")
            st.write("")
            if chart_type == "Bar":
                horizontal = st.checkbox("Afficher le graphique horizontalement")
                stack = st.checkbox("Stacker les sous-catégories")
                stack_100 = st.checkbox("Stack 100%")
                st.write(" ")
                if stack_100 == True:
                    stack = 'normalize'
                st.bar_chart(df, 
                             use_container_width=True,  
                             height=600, 
                             horizontal=horizontal, 
                             stack=stack, 
                             y_label={index_cols[0]} if horizontal else {agg_func_fr + " de : " + value_col}, 
                             x_label={agg_func_fr + " de : " + value_col} if horizontal else {index_cols[0]}
                             )
            elif chart_type == "Line":
                st.line_chart(df, 
                              use_container_width=True, 
                              height=600,
                              y_label={agg_func_fr + " de : " + value_col}, 
                              x_label={index_cols[0]}
                              )
            elif chart_type == "Area":
                st.area_chart(df, 
                              use_container_width=True, 
                              height=600,
                              y_label={agg_func_fr + " de : " + value_col}, 
                              x_label={index_cols[0]}
                              )
        else:
            st.warning("_La représentation graphique est disponible avec 2 dimensions._\n\n_Selectionnez seulement une ligne et une colonne_")
    elif index_col_count == 0:
        st.write("")
        st.warning("_Veuillez choisir au moins une ligne pour afficher le tableau croisé et un graphique_")
# Main Streamlit App
if __name__ == "__main__":
    st.title("💊 Easy Open Medic")
    st.success("_Les bases open medic sont complexes à utiliser, ce site est destiné à vous faciliter la tache ;)_\n\n_Les données Open Medic présentent *l’ensemble des prescriptions de médicaments délivrés en officine de ville* en France, que le prescripteur soit libéral ou salarié (prescriptions hospitalières principalement)._")
    
    st_supabase_client = st.connection(
    name="public",
    type=SupabaseConnection,
    ttl=None,
    )

    # Medication Search
    st.subheader("🔍 Recherche par médicament (DCI) ou classe ATC3")
    
    #SELECT A DRUG ENTRY POINT
    atc5_df = fetch_atc5()
    atc5_display_values = atc5_df['L_ATC5'].tolist()
    selected_display_value = st.selectbox(
        label="", 
        options=atc5_display_values, 
        placeholder="Choisir un médicament (DCI)",
        index=None
    )

    selected_value_df = atc5_df.loc[atc5_df['L_ATC5'] == selected_display_value, 'ATC5']
    if not selected_value_df.empty:
        selected_atc5 = selected_value_df.iat[0]
    else:
        selected_atc5 = None

    if selected_atc5 is None:
        atc3_df = fetch_atc3()
        atc3_display_values = atc3_df['L_ATC3'].tolist()
        st.write("Ou...")
        selected_display_value_atc3 = st.selectbox(
            label="", 
            options=atc3_display_values,
            key="selected_atc3", 
            placeholder="Selectionner une classe ATC3 🤓...",
            index=None
        )
        selected_value_df_atc3 = atc3_df.loc[atc3_df['L_ATC3'] == selected_display_value_atc3, 'ATC3']
        if not selected_value_df_atc3.empty:
            selected_atc3 = selected_value_df_atc3.iat[0]
            selected_atc3_label = selected_display_value_atc3
        else:
            selected_atc3 = None
            selected_atc3_label = None

    if selected_atc5:
        st.header(selected_display_value)
        fetch_column = 'Code ATC5'
        fetch_value = selected_atc5
        
    if selected_atc3:
        st.header(selected_atc3_label)
        fetch_column = 'Code ATC3'
        fetch_value = selected_atc3

    st.divider()

    if selected_atc5 or selected_atc3:    
        open_medic_table = fetch_data(fetch_column, fetch_value)   
        st.subheader(":blue[Tableau de données brutes:]") 
        st.dataframe(open_medic_table, height=100)
        if len(open_medic_table) == 200000:
            st.write(f"_Nombre de lignes : {len(open_medic_table)} - Attention, dataset incomplet, seuls les 200000 premières lignes sont prises en compte_")
        else:
            st.write(f"_Nombre de lignes : {len(open_medic_table)}_")
        st.divider()

        pivot_table, index_col_count, column_col_count, agg_func_fr, value_col, index_cols = create_pivot_table(open_medic_table)
        visualize_data(pivot_table, index_col_count, column_col_count, agg_func_fr , value_col, index_cols)
        
    if selected_atc3 == None and selected_atc5 == None:
        st.info("_Les temps de chargement peuvent être un peu long, mais toujours moins longs que 10 millions de lignes sur excel 💚_")

