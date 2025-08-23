import json


# Tax brackets are always the same between the regions
# However progressive rates are different -> store them separately


def load_tax_data_from_json(file_path: str) -> dict:
    """
    Loads tax data from a JSON file.
    
    Args:
        file_path (str): The path to the JSON file.
    
    Returns:
        dict: A dictionary containing the tax data.
    """
    try:
        with open(file_path, "r") as file:
            tax_data_json = json.load(file)
        return tax_data_json
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Failed to decode the JSON file. Please check for syntax errors.")
        return None


def get_tax_data(year: int, region: str) -> dict:
    """
    Retrieves the tax data (brackets, rates, and IAS) for a given year and region.

    Args:
        year (int): The tax year (e.g., 2023, 2024, 2025).
        region (Region): The geographical region (e.g., 'Madeira').

    Returns:
        dict: A dictionary containing the tax brackets, rates, and IAS value.
              Returns None if the data is not found.
    """
    year = str(year)
    tax_data = load_tax_data_from_json("rates.json")
    if tax_data and year in tax_data and region in tax_data[year]:
        return tax_data[year][region]
    else:
        print(f"Error: No tax data found for year {year} and region {region}.")
        return None