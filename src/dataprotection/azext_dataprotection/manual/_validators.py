# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Dict, Any, Union
from azure.cli.core.commands.validators import (
    validate_file_or_dict
)
from dateutil import parser


def datetime_type(string: str) -> str:
    """
    Validate UTC datetime in accepted format.
    
    Args:
        string: DateTime string to parse (Examples: 2017-12-31, 2017-12-31T05:30:00)
        
    Returns:
        Formatted datetime string in ISO format with timezone
        
    Raises:
        ValueError: If the input string is not a valid datetime format
    """
    try:
        newtime = parser.isoparse(string).strftime("%Y-%m-%dT%H:%M:%S.%f") + "0Z"
        return newtime
    except ValueError:
        raise ValueError(f"Input '{string}' not valid. Valid example: 2017-12-31T05:30:00")


def schedule_days_type(string: str) -> str:
    """
    Validate schedule days string input.
    
    Args:
        string: Input string to validate
        
    Returns:
        The validated string
        
    Raises:
        ValueError: If the string is empty or None
    """
    if not string:
        raise ValueError("Schedule days string cannot be empty")
    return string


def namespaced_name_resource_type(list_of_dict: Union[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
    """
    Validate namespaced name resource type input.
    
    Args:
        list_of_dict: List of dictionaries or JSON string containing name and namespace pairs
        
    Returns:
        Validated list of dictionaries with 'name' and 'namespace' keys
        
    Raises:
        ValueError: If input is not valid or dictionaries don't have required keys
    """
    list_of_dict = validate_file_or_dict(list_of_dict)
    for dictionary in list_of_dict:
        if not (len(dictionary) == 2 and 'name' in dictionary and 'namespace' in dictionary):
            raise ValueError(f"Input {list_of_dict} is not valid. Keys should be 'name' and 'namespace'.")
    return list_of_dict
