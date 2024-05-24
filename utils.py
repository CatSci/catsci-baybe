from baybe import Campaign
from baybe.objective import Objective
from baybe.parameters import NumericalDiscreteParameter, SubstanceParameter
from baybe.searchspace import SearchSpace
from baybe.targets import NumericalTarget
import streamlit as st
import pandas as pd
import json

def convert_categorical_variable(cat_dict, name):
    """_summary_

    Args:
        cat_dict (_type_): _description_
        name (_type_): _description_
    """
    return SubstanceParameter(name, data=cat_dict, encoding="MORDRED")



def convert_numerical_variable(num_list, name):
    """_summary_

    Args:
        numerical_variables_dict (_type_): _description_
    """
    return NumericalDiscreteParameter(name, values= num_list)



def convert_objective_variable(name, mode):
    """_summary_

    Args:
        name (_type_): _description_
        mode (_type_): _description_
    """

    return NumericalTarget(name= name, mode= mode, bounds=(0, 100), transformation="LINEAR")




def convert_params(categorical_variables_dict, numerical_variables_dict, objective_dict) -> list:
    parameters = []
    objectives = []
    """_summary_

    Args:
        categorical_variables_dict (_type_): _description_
        numerical_variables_dict (_type_): _description_

    Returns:
        list: _description_
    """
    for cat in categorical_variables_dict:
        
        variable = convert_categorical_variable(cat_dict= categorical_variables_dict[cat], name = cat)
        parameters.append(variable)

    for numerical in numerical_variables_dict:
        variable = convert_numerical_variable(num_list = numerical_variables_dict[numerical], name = numerical)
        parameters.append(variable)
    
    
    for obj in objective_dict:
        target = convert_objective_variable(name = obj, mode= objective_dict[obj][0].upper())
        objectives.append(target)

    return parameters, objectives


def create_campaign(categorical_variables_dict, numerical_variables_dict, objective_dict, strategy, weights):
    """_summary_

    Args:
        categorical_variables_dict (_type_): _description_
        numerical_variables_dict (_type_): _description_
        objective_dict (_type_): _description_

    Returns:
        _type_: _description_
    """
    parameters, objectives = convert_params(categorical_variables_dict, numerical_variables_dict, objective_dict)
    searchspace = SearchSpace.from_product(parameters=parameters)
    if len(objectives) > 1:
        mode = "DESIRABILITY"
    else:
        mode = "SINGLE"

    objective = Objective(mode= mode,targets=objectives, weights= weights)
    campaign = Campaign(searchspace=searchspace,objective=objective, recommender= strategy)

    return campaign.to_json()




def recommend_reactions(campaign, df, batch_reactions)-> pd.DataFrame:
    recommendations = None
    campaign_recreate = None
    if campaign:
        campaign_recreate = Campaign.from_json(campaign)
        campaign_json = json.loads(campaign)
        target_list = campaign_json.get("objective")["targets"]
        target_names = [target["name"] for target in target_list]

        if df is None:
            recommendations = campaign_recreate.recommend(batch_size= batch_reactions)
            for target_column in target_names:
                recommendations[target_column] = None
        else:
            campaign_recreate.add_measurements(df)
            recommendations = campaign_recreate.recommend(batch_size= batch_reactions)
            for target_column in target_names:
                recommendations[target_column] = None
        
    else:
        st.error("Please upload valid file")

    return recommendations, campaign_recreate.to_json() if campaign_recreate else None
