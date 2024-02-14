import streamlit as st
from utils import convert_params, create_campaign, recommend_reactions
from baybe.searchspace import SearchSpace
from baybe import Campaign
from baybe.objective import Objective
from baybe.targets import NumericalTarget
from baybe.recommenders import RandomRecommender, FPSRecommender, KMeansClusteringRecommender, SequentialGreedyRecommender
from baybe.strategies import TwoPhaseStrategy
from baybe.surrogates import (
    BayesianLinearSurrogate,
    GaussianProcessSurrogate,
    NGBoostSurrogate,
    RandomForestSurrogate,
)
import json
from io import StringIO
import pandas as pd


ACQ_FUNCTION = "qEI"
ALLOW_REPEATED_RECOMMENDATIONS = True
ALLOW_RECOMMENDING_ALREADY_MEASURED = True


# Map the function names to the actual functions using a dictionary
strategy_functions_first = {
    'Random': RandomRecommender(),
    'Farthest Point Sampling': FPSRecommender(),
    'KMEANS Clustering': KMeansClusteringRecommender(),
}

strategy_functions_second = {
    "Gaussian Process" : GaussianProcessSurrogate(),
    "Random Forest": RandomForestSurrogate(),
    "NGBoost": NGBoostSurrogate(),
    "Bayesian Linear": BayesianLinearSurrogate(),
}

def create_categorical_fields(num_variables):
    variable_dict = {}
    for i in range(num_variables):
        variable_name = st.text_input(f"Variable {i + 1} title:", placeholder = 'Solvent')
        variable_values = st.text_input(f"Variable {i + 1} name (comma-separated):", placeholder= "DMAc")
        variable_smile_values = st.text_input(f"Variable {i + 1} smile values (comma-separated):", placeholder= "CC(N(C)C)=O")

        keys = [value.strip() for value in variable_values.split(',')]
        values = [value.strip() for value in variable_smile_values.split(',')]
    
        variable_dict[variable_name] = dict(zip(keys, values))
    # st.write(variable_dict)
    return variable_dict


def create_numerical_fields(num_numerical_variables):
    variable_dict = {}
    for i in range(num_numerical_variables):
        variable_name = st.text_input(f"Variable {i + 1} name:", placeholder = 'Temperature')
        variable_values = st.text_input(f"Variable {i + 1} value (comma-separated):", placeholder= "90,105,120")
        values = [value.strip() for value in variable_values.split(',')]

        variable_dict[variable_name] = values
    return variable_dict


def create_objective_fields(num_objective_variables):
    objective_dict = {}
    for i in range(num_objective_variables):
        variable_name = st.text_input(f"Objective {i + 1} name:", placeholder = 'Yield')
        variable_values = st.text_input(f"Objective {i + 1} mode (comma-separated):", placeholder= "max")
        # weights = st.number_input()
        values = [value.strip() for value in variable_values.split(',')]

        objective_dict[variable_name] = values
    # st.write(objective_dict)
    return objective_dict


def upload_file(key):
    uploaded_files = st.file_uploader("Choose a CSV file", key = key)
    
    if uploaded_files is not None and uploaded_files.name.split('.')[1] == 'json':
        stringio = StringIO(uploaded_files.getvalue().decode("utf-8"))
        data = stringio.read()
        # st.json(data)
        return data
    
    if uploaded_files is not None and uploaded_files.name.split('.')[1] == 'csv':
        df = pd.read_csv(uploaded_files)
        return df


def recommend_input():
    past_recommendation = st.checkbox('Do you have previous recommended reactions data')
    if past_recommendation:
        df = upload_file(key= 'csv')
        return df
        

def main():
    st.title("Bayesian Reaction Optimizer")
    tab1, tab2 = st.tabs(["Create Scope", "Optimize"])

    # Store the initial value of widgets in session state
    if "visibility" not in st.session_state:
        st.session_state.visibility = "visible"
        st.session_state.disabled = False

    with tab1:
        st.header("Create Scope")
        col1, col2 = st.columns(2)
        with col1:
            num_categorical_variables = st.number_input("How many **categorical** variables do you have?", min_value=0, value=0, key = 'cat')
            categorical_variables_dict = create_categorical_fields(num_categorical_variables)
        with col2:
            num_numerical_variables = st.number_input("How many **numerical** variables do you have?", min_value=0, value=0, key = 'num')
            numerical_variables_dict = create_numerical_fields(num_numerical_variables)

        num_objectives = st.number_input("How many **objective** variables do you have", min_value= 0, value= 0, key = 'obj')
        objective_dict = create_objective_fields(num_objectives)
        objective_weights = st.text_input("Target Objective weights (comma-separated):", placeholder= "50,50")
        vals = objective_weights.split(',')
        weights = [int(value.strip()) for value in vals if value.strip().isdigit()]

        
        initial_recommender = st.selectbox(
            'For the first recommendation, which strategy to use?',
            ('Random', 'Farthest Point Sampling', 'KMEANS Clustering'))
        
        second_recommender = st.selectbox(
            "For the second recommendation, which strategy to use?",
            ("Gaussian Process", "Random Forest","NGBoost","Bayesian Linear"))
        
        # initial_recommender = strategy_functions_first[initial_recomender]
        # sequential_recommender = SequentialGreedyRecommender(
        #     surrogate_model=strategy_functions_second[second_recomender],
        #     acquisition_function_cls=ACQ_FUNCTION)
            
        strategy = TwoPhaseStrategy(
                        initial_recommender= strategy_functions_first[initial_recommender],
                        recommender=SequentialGreedyRecommender(
                            surrogate_model= strategy_functions_second[second_recommender], acquisition_function_cls=ACQ_FUNCTION
                        ),)
                        # allow_repeated_recommendations=ALLOW_REPEATED_RECOMMENDATIONS,
                        # allow_recommending_already_measured=ALLOW_RECOMMENDING_ALREADY_MEASURED)

        if st.button('Create Scope'):
            with st.spinner('Wait for it...'):                    
                campaign_json = create_campaign(categorical_variables_dict, numerical_variables_dict, objective_dict, strategy, weights)
                st.download_button("Download", campaign_json, file_name= 'campaign.json')
        
    with tab2:
        st.header("Recommend Reactions")
        campaign_previous = upload_file(key= 'json')
        batch_quantity = st.number_input("Select **batch size**", min_value= 1, value= 1, key = 'batch')
        df = recommend_input()
        reactions, new_campaign = recommend_reactions(campaign_previous, df, batch_quantity)
        if st.button("Get recommendations"):
            if reactions is not None and new_campaign is not None:
                st.data_editor(reactions)
                st.download_button("Download JSON file", new_campaign, file_name= "campaign.json")
                # st.download_button("Download recommended reactions", reactions.to_csv().encode('utf-8'), file_name= 'reactions.csv', mime= 'text/csv')
                # st.write(reactions)

        # if new_campaign is not None:
        #     st.json(new_campaign)





if __name__ == "__main__":
    main()